import ast
import argparse
import os
from collections import deque

class VariableCollector(ast.NodeVisitor):
    def __init__(self):
        self.variables = set()

    def visit_Call(self, node):
        # Check if the function call is a method call on an object
        if isinstance(node.func, ast.Attribute):
            # If it's an attribute, add the object being called
            self.visit(node.func.value)

        for arg in node.args:
            self.visit(arg)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.variables.add(node.id)
    
    def visit_If(self, node):
        self.visit(node.test)
    
    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            self.variables.add(node.value.id)
        self.visit(node.value)

    def generic_visit(self, node):
        # Visit all child nodes
        for child in ast.iter_child_nodes(node):
            self.visit(child)

def get_variables_used(stmt):
    collector = VariableCollector()
    collector.visit(stmt)
    return set(collector.variables)

class AwaitMover(ast.NodeTransformer):
    def __init__(self, external_functions, async_funcs):
        self.external_functions = set(external_functions)
        self.async_funcs = async_funcs
        self.nesting = 0
        # stores all variable dependencies
        self.var_dependencies = {}
        self.all_awaits = set()
    
    def visit_AsyncFunctionDef(self, node):
        if node.name not in self.async_funcs:
            return node

        is_main_method = any(
            isinstance(dec, ast.Name) and dec.id == "main_method"
            for dec in node.decorator_list
        )

        self.nesting = 0
        self.var_dependencies.clear()
        self.all_awaits = set()
        
        # get comments
        docstring = ast.get_docstring(node)
        if docstring:
            node.body = [stmt for stmt in node.body if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str))]
            node.body.insert(0, ast.Expr(ast.Str(s=docstring)))

        pending_awaits_init = ast.Assign(
            targets=[ast.Name(id='pending_awaits', ctx=ast.Store())],
            value=ast.List(elts=[], ctx=ast.Load())
        )
        node.body.insert(0, pending_awaits_init)
        node.body = self.process_body(node.body)
        
        if is_main_method:
            # Find the return statement
            for i, stmt in enumerate(node.body):
                if isinstance(stmt, ast.Return):
                    # Insert the await loop before the return
                    node.body.insert(i, self.create_await_loop())
                    break
            else:
                # If no return statement found, append the await loop
                node.body.append(self.create_await_loop())
        return node
    
    def process_body(self, body):
        self.nesting += 1
        current_awaits = self.all_awaits.copy()
        local_awaits =set()
        
        temp_body = []
        final_body = []
        
        for stmt in body:
            stmt = self.visit(stmt)
            variables_used = get_variables_used(stmt)

            if self.is_await_call(stmt):

                self.all_awaits.add(stmt)

                await_variable_names = self.get_await_variable_name(stmt)

                for name in await_variable_names:
                    self.var_dependencies[name] = stmt

                current_awaits.add(stmt)
                local_awaits.add(stmt)
            
            elif self.is_async_function_call(stmt):
                # Get the function name
                func_name = stmt.value.func.id
                # Create new variable name for the pending awaits
                pending_var = f'pending_awaits_{func_name}'
                # Transform func() into pending_awaits_func = func()
                assign_stmt = ast.Assign(
                    targets=[ast.Name(id=pending_var, ctx=ast.Store())],
                    value=stmt.value
                )
                temp_body.append(assign_stmt)
                
                # Add pending_awaits.extend(pending_awaits_func)
                extend_stmt = ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='pending_awaits', ctx=ast.Load()),
                            attr='extend',
                            ctx=ast.Load()
                        ),
                        args=[ast.Name(id=pending_var, ctx=ast.Load())],
                        keywords=[]
                    )
                )
                temp_body.append(extend_stmt)

            elif variables_used.intersection(self.var_dependencies.keys()):
                final_body.extend(temp_body)

                variables_to_remove = variables_used.intersection(self.var_dependencies.keys())
                
                for variable_name in variables_to_remove:
                    stmt_append = self.var_dependencies[variable_name]
                    final_body.append(stmt_append)

                    # we don't want to dump this at the end
                    current_awaits.discard(stmt_append)
                    local_awaits.discard(stmt_append)

                    # if this is main level, we can be sure we awaited the whole dependency
                    if self.nesting == 1:
                        del self.var_dependencies[variable_name]
                temp_body = []

                if self.is_return_statement(stmt):
                    final_body.extend(temp_body)
                    append_stmt = self.extend_pending_awaits(list(current_awaits))
                    final_body.append(append_stmt)

                    # Create a new return statement that returns pending_awaits
                    if stmt.value:
                        stmt.value = ast.Tuple(
                            elts=[
                                stmt.value,
                                ast.Name(id='pending_awaits', ctx=ast.Load())
                            ],
                            ctx=ast.Load()
                        )
                    else:
                        # If empty return, just return pending_awaits
                        stmt.value = ast.Name(id='pending_awaits', ctx=ast.Load())

                    final_body.append(stmt)

                    if self.nesting == 1:
                        self.var_dependencies.clear()
                        self.all_awaits = set()
                    
                    current_awaits = set()
                    local_awaits = set()
                    temp_body = []

                final_body.append(stmt)
            elif self.is_return_statement(stmt) or self.is_external_function_call(stmt):
                final_body.extend(temp_body)

                # awaits_to_add = list(current_awaits)
                # final_body.extend(awaits_to_add)
                append_stmt = self.extend_pending_awaits(list(current_awaits))
                final_body.append(append_stmt)

                if self.is_return_statement(stmt):
                    # Replace the return value with pending_awaits
                    stmt.value = ast.Name(id='pending_awaits', ctx=ast.Load())

                final_body.append(stmt)

                if self.nesting == 1:
                    self.var_dependencies.clear()
                    self.all_awaits = set()
                current_awaits = set()
                local_awaits = set()
                temp_body = []
            else:
                temp_body.append(stmt)
        # Combine the processed statements
        final_body.extend(temp_body)

        # final_body.extend(local_awaits)

        for awt in local_awaits:
            self.all_awaits.discard(awt)
            current_awaits.discard(awt)

            await_variable_name = self.get_await_variable_name(awt)
            for name in await_variable_name:
                del self.var_dependencies[name]
        local_awaits = set()

        if self.nesting == 1:
            # final_body.extend(current_awaits)
            self.var_dependencies.clear()
            self.all_awaits = set()

            if not any(isinstance(node, ast.Return) for node in final_body):
                final_body.append(ast.Return(
                    value=ast.Name(id='pending_awaits', ctx=ast.Load())
                ))

        self.nesting -= 1
        return final_body

    def extend_pending_awaits(self, awaits):
        append_stmt = ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='pending_awaits', ctx=ast.Load()),
                    attr='extend',
                    ctx=ast.Load()
                ),
                args=[
                    ast.List(
                        elts=[await_stmt.value.value for await_stmt in awaits],
                        ctx=ast.Load()
                    )
                ],
                keywords=[]
            )
        )
        return append_stmt

    def get_await_variable_name(self, stmt):
        # Check for assignment statements where the value is an await expression
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Await):
            target = stmt.targets[0]
            if isinstance(target, ast.Name):
                return [target.id]
            elif isinstance(target, ast.Tuple):  # Handle tuple assignments
                return [name.id for name in target.elts if isinstance(name, ast.Name)]
            elif isinstance(target, ast.Attribute):  # Handle attributes, e.g., obj.attr = await ...
                return [target.attr]
        # Check for expression statements where the expression is an await
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Await):
            if isinstance(stmt.value.value, ast.Name):
                return [stmt.value.value.id]
        return None

    def is_async_function_call(self, stmt):
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            if isinstance(stmt.value.func, ast.Name):
                return stmt.value.func.id in self.async_funcs
        return False

    def is_await_call(self, node):
        return (
            (isinstance(node, ast.Expr) and isinstance(node.value, ast.Await)) or
            (isinstance(node, ast.Assign) and isinstance(node.value, ast.Await))
        )

    def is_external_function_call(self, node):
        return (isinstance(node, ast.Expr) and
                isinstance(node.value, ast.Call) and
                isinstance(node.value.func, ast.Name) and
                node.value.func.id in self.external_functions)

    def is_return_statement(self, node):
        return isinstance(node, ast.Return)
    
    def visit_If(self, node):
        node.body = self.process_body(node.body)
        if node.orelse:
            if isinstance(node.orelse[0], ast.If):
                node.orelse = [self.visit(node.orelse[0])]
            else:
                node.orelse = self.process_body(node.orelse)
        return node
    
    def create_await_loop(self):
        """Creates an AST for looping through and awaiting pending_awaits"""
        return ast.For(
            target=ast.Name(id='await_stmt', ctx=ast.Store()),
            iter=ast.Name(id='pending_awaits', ctx=ast.Load()),
            body=[
                ast.Expr(
                    value=ast.Await(
                        value=ast.Name(id='await_stmt', ctx=ast.Load())
                    )
                )
            ],
            orelse=[]
        )

def main():
    parser = argparse.ArgumentParser(description="Transform async code to append all awaits at the bottom.")
    parser.add_argument('input_files', nargs='+', help="The Python file(s) to transform")
    args = parser.parse_args()

    output_dir = os.path.join('..', 'output')
    os.makedirs(output_dir, exist_ok=True)

    for input_file in args.input_files:
        with open(input_file, 'r') as f:
            source_code = f.read()

        tree = ast.parse(source_code)
        transformer = AwaitMover()
        transformed_tree = transformer.visit(tree)
        ast.fix_missing_locations(transformed_tree)
        
        new_source_code = ast.unparse(transformed_tree)

        output_file = input_file.replace('.py', '_down.py')
        output_file_path = os.path.join(output_dir, os.path.basename(output_file))
        
        with open(output_file_path, 'w') as f:
            f.write(new_source_code)

        print(f"Transformed code has been written to {output_file_path}.")

if __name__ == "__main__":
    main()

def await_push(source_code,external_functions, asnyc_functions):
    tree = ast.parse(source_code)
    transformer = AwaitMover(external_functions, asnyc_functions)
    transformer.current_node = tree
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    return ast.unparse(transformed_tree)