import ast
import argparse
import os

class AsyncFuturePushUp(ast.NodeTransformer):
    def __init__(self):
        self.ensure_future_calls = []
        # self.await_statements = {}
        self.variable_uses = {}
        self.used_awaits = set()

    def visit_AsyncFunctionDef(self, node):
        self.ensure_future_calls = []
        # self.await_statements = {}
        self.variable_uses = {}
        self.used_awaits = set()

        # First pass: collect ensure_future calls and await statements
        for stmt in node.body:
            self.visit(stmt)

        # Second pass: reorder statements
        new_body = []
        for call in self.ensure_future_calls:
            new_body.append(call)

        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Attribute) and stmt.value.func.attr == 'ensure_future':
                continue  # Skip ensure_future assignments as they're already at the top

            # Insert await statements just before their variables are used
            # for var, index in list(self.variable_uses.items()):
            #     if index == len(new_body):
            #         if var in self.await_statements and var not in self.used_awaits:
            #             new_body.append(self.await_statements[var])
            #             self.used_awaits.add(var)
            new_body.append(stmt)

        # Add any remaining await statements at the end (only if not used before)
        # for var, await_stmt in self.await_statements.items():
        #     if var not in self.used_awaits:
        #         new_body.append(await_stmt)

        node.body = new_body
        return node

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == 'ensure_future':
            self.ensure_future_calls.append(node)
            if isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                self.variable_uses[var_name] = float('inf')
        else:
            self.generic_visit(node)
        return node

    # def visit_Await(self, node):
    #     if isinstance(node.value, ast.Name):
    #         var_name = node.value.id
    #         self.await_statements[var_name] = ast.Expr(value=node)
    #     return ast.Pass()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            if node.id in self.variable_uses and self.variable_uses[node.id] == float('inf'):
                self.variable_uses[node.id] = len(self.variable_uses)
        return node

def main():
    parser = argparse.ArgumentParser(description="Transform async code to move ensure_future calls to the top and insert awaits before variable uses.")
    parser.add_argument('input_files', nargs='+', help="The Python file(s) to transform")
    args = parser.parse_args()

    output_dir = os.path.join('..', 'output')
    os.makedirs(output_dir, exist_ok=True)

    for input_file in args.input_files:
        with open(input_file, 'r') as f:
            source_code = f.read()

        tree = ast.parse(source_code)
        transformer = AsyncFuturePushUp()
        transformed_tree = transformer.visit(tree)
        ast.fix_missing_locations(transformed_tree)
        
        new_source_code = ast.unparse(transformed_tree)

        output_file = input_file.replace('.py', '_push.py')
        output_file_path = os.path.join(output_dir, os.path.basename(output_file))
        
        with open(output_file_path, 'w') as f:
            f.write(new_source_code)

        print(f"Transformed code has been written to {output_file_path}.")

if __name__ == "__main__":
    main()
