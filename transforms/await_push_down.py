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
    def __init__(self, external_functions):
        self.external_functions = set(external_functions)
        self.nesting = 0
        # stores all variable dependencies
        self.var_dependencies = {}
        self.all_awaits = set()
    
    def visit_AsyncFunctionDef(self, node):
        self.nesting = 0
        self.var_dependencies.clear()
        self.all_awaits = set()
        
        # get comments
        docstring = ast.get_docstring(node)
        if docstring:
            node.body = [stmt for stmt in node.body if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str))]
            node.body.insert(0, ast.Expr(ast.Str(s=docstring)))
    
        node.body = self.process_body(node.body)
        return node
    
    def process_body(self, body):
        self.nesting += 1
        # local_awaits = set()
        # grab for all possible dependencies
        # pass this as a set
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

            elif variables_used.intersection(self.var_dependencies.keys()):
                final_body.extend(temp_body)

                variables_to_remove = variables_used.intersection(self.var_dependencies.keys())
                
                for variable_name in variables_to_remove:
                    stmt_append = self.var_dependencies[variable_name]
                    final_body.append(stmt_append)

                    # we don't want to dump this at the end
                    current_awaits.discard(stmt_append)
                    local_awaits.discard(stmt_append)

                    # print("Found dependency", variable_name, self.nesting)

                    # if this is main level, we can be sure we awaited the whole dependency
                    if self.nesting == 1:
                        del self.var_dependencies[variable_name]
                        # print("Deleted", variable_name)
                temp_body = []

                if self.is_return_statement(stmt):
                    final_body.extend(temp_body)

                    # dump current awaits
                    awaits_to_add = list(current_awaits)
                    final_body.extend(awaits_to_add)

                    # if main execution level, this is last return
                    if self.nesting == 1:
                        self.var_dependencies.clear()
                        self.all_awaits = set()
                    
                    current_awaits = set()
                    local_awaits = set()
                    temp_body = []

                final_body.append(stmt)
            elif self.is_return_statement(stmt) or self.is_external_function_call(stmt):
                final_body.extend(temp_body)

                awaits_to_add = list(current_awaits)
                final_body.extend(awaits_to_add)
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

        final_body.extend(local_awaits)

        for awt in local_awaits:
            self.all_awaits.discard(awt)
            current_awaits.discard(awt)

            await_variable_name = self.get_await_variable_name(awt)
            for name in await_variable_name:
                del self.var_dependencies[name]
        local_awaits = set()

        if self.nesting == 1:
            final_body.extend(current_awaits)
            self.var_dependencies.clear()
            self.all_awaits = set()

        self.nesting -= 1
        return final_body

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

def await_push(source_code,external_functions):
    tree = ast.parse(source_code)
    transformer = AwaitMover(external_functions)
    transformer.current_node = tree
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    return ast.unparse(transformed_tree)
