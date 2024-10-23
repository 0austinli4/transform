import ast
import argparse
import os
from collections import deque

class VariableCollector(ast.NodeVisitor):
    def __init__(self):
        self.variables = set()

    def visit_Call(self, node):
        # Visit all arguments of the function call
        for arg in node.args:
            self.visit(arg)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.variables.add(node.id)
    
    def visit_If(self, node):
        # Visit the test condition of the if statement
        self.visit(node.test)
        # Visit the body and orelse parts

        # for stmt in node.body + node.orelse:
        #     self.visit(stmt)

    def visit_Attribute(self, node):
        # For attributes, we're only interested in the base name
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
        print("\n\nStart of push down class")
        self.external_functions = set(external_functions)
        self.nesting = 0
        self.var_dependencies = {}
        self.global_awaits = {}
    
    def visit_AsyncFunctionDef(self, node):
        self.nesting = 0
        self.var_dependencies.clear()
        self.global_awaits.clear()
        
        # get comments
        docstring = ast.get_docstring(node)
        if docstring:
            node.body = [stmt for stmt in node.body if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str))]
            node.body.insert(0, ast.Expr(ast.Str(s=docstring)))
        
        node.body = self.process_body(node.body)
        return node
    
    def process_body(self, body):
        print("\n\nAt the top of body, reset all")
        self.nesting += 1
        local_awaits = {}
        temp_body = []
        final_body = []
        
        for stmt in body:
            stmt = self.visit(stmt)

            variables_used = get_variables_used(stmt)

            if self.is_await_call(stmt):
                await_variable_name = self.get_await_variable_name(stmt)
                print("Adding await call", await_variable_name)
                self.global_awaits[await_variable_name] = stmt
                local_awaits[await_variable_name] = stmt
                print("Hit await first time ", await_variable_name)
            elif variables_used.intersection(self.global_awaits.keys()):
                final_body.extend(temp_body)
                variables_remove = variables_used.intersection(self.global_awaits.keys())
                print("Found dependency", variables_remove)
                print("Current local await", local_awaits)

                for variable_name in variables_remove:
                    final_body.append(self.global_awaits[variable_name])
                    if self.nesting == 1:
                        del self.global_awaits[variable_name]
                        print("removing", self.global_awaits)
                    if variable_name in local_awaits:
                        del local_awaits[variable_name]
                temp_body = []

                # don't have anything after a return statements
                if self.nesting == 1 and self.is_return_statement(stmt):
                    print("last return statement")
                    final_body.extend(self.global_awaits.values())
                    self.global_awaits.clear()
                    local_awaits = {}
                final_body.append(stmt)
            elif self.is_external_function_call(stmt):
                # If we hit an external function call, process collected calls
                final_body.extend(temp_body)
                final_body.extend(self.global_awaits.values())
                self.global_awaits.clear()
                local_awaits = {}
                final_body.append(stmt)
                temp_body = []
            elif self.is_return_statement(stmt):
                print("This is a return statement", self.nesting)
                final_body.extend(temp_body)
                final_body.extend(self.global_awaits.values())
                final_body.append(stmt)
                if self.nesting == 1:
                    self.global_awaits.clear()
                local_awaits = {}
                temp_body = []
            else:
                stmt = self.visit(stmt)
                temp_body.append(stmt)

        # Combine the processed statements
        final_body.extend(temp_body)

        print("Finished local, extending awaits", local_awaits.keys())
        
        final_body.extend(local_awaits.values())

        common_keys = set(self.global_awaits.keys()).intersection(local_awaits.keys())

        # Remove these keys from dict1
        for key in common_keys:
            del self.global_awaits[key]
        
        local_awaits = {}

        # print("Current body nesting level", self.nesting, self.global_awaits)
        if self.nesting == 1:
            print('End of body, returning global', self.global_awaits.values())
            final_body.extend(self.global_awaits.values())
            self.global_awaits.clear()
            
        self.nesting -= 1 
        print("Returning final body")
        return final_body

    def get_await_variable_name(self, stmt):
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Await):
            if isinstance(stmt.targets[0], ast.Name):
                return stmt.targets[0].id
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Await):
            if isinstance(stmt.value.value, ast.Name):
                return stmt.value.value.id
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

    # def visit_If(self, node):
    #     node.body = self.process_body(node.body)
    #     if node.orelse:
    #         if isinstance(node.orelse[0], ast.If):
    #             node.orelse = [self.visit(node.orelse[0])]
    #         else:
    #             node.orelse = self.process_body(node.orelse)
    #     # node.orelse = self.process_body(node.orelse)
    #     return node


    # def visit_Call(self, node):
    #     if isinstance(node.func, ast.Attribute) and node.func.attr == 'ensure_future':
    #         if isinstance(node.args[0], ast.Call):
    #             var_name = self.get_assigned_var(node)
    #             if var_name:
    #                 self.current_scope[var_name] = ast.Await(value=node.args[0])
    #     return node

    # def get_assigned_var(self, node):
    #     parent = self.parent_map.get(node)
    #     if isinstance(parent, ast.Assign) and len(parent.targets) == 1:
    #         target = parent.targets[0]
    #         if isinstance(target, ast.Name):
    #             return target.id
    #     return None

    # def insert_awaits(self, body):
    #     new_body = []
    #     for stmt in body:
    #         new_body.append(stmt)
    #         if isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0], ast.Name):
    #             var_name = stmt.targets[0].id
    #             if var_name in self.current_scope:
    #                 new_body.append(ast.Expr(value=self.current_scope[var_name]))
    #                 del self.current_scope[var_name]
    #     return new_body

    # def visit(self, node):
    #     self.parent_map = {child: node for child in ast.walk(node) for node in ast.walk(child)}
    #     return super().visit(node)


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
