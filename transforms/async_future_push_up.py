import ast
import argparse
import os

class AsyncFuturePushUp(ast.NodeTransformer):
    def __init__(self):
        self.ensure_future_calls = []
        self.variable_uses = {}
    def visit_AsyncFunctionDef(self, node):
        self.ensure_future_calls = []
        self.variable_uses = {}

        # First pass: collect top-level ensure_future calls
        new_body = []
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Attribute) and stmt.value.func.attr == 'ensure_future':
                self.ensure_future_calls.append(stmt)
            else:
                new_body.append(self.visit(stmt))

        # Second pass: reorder statements
        final_body = self.ensure_future_calls + new_body
        node.body = final_body
        return node

    def visit_Await(self, node):
        # Keep await statements as they are
        return node

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == 'ensure_future':
            if isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                self.variable_uses[var_name] = float('inf')
        return node

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            if node.id in self.variable_uses and self.variable_uses[node.id] == float('inf'):
                self.variable_uses[node.id] = len(self.variable_uses)
        return node

def main():
    parser = argparse.ArgumentParser(description="Transform async code to move ensure_future calls to the top and insert awaits before variable uses.")
    parser.add_argument('input_files', nargs='+', help="The Python file(s) to transform")
    args = parser.parse_args()

    output_dir = os.path.join('output')
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
