import ast
import argparse
import os

class AwaitMover(ast.NodeTransformer):
    def __init__(self):
        self.future_calls = {}
        self.scopes = [{}]
        self.current_scope = self.scopes[-1]

    def visit_AsyncFunctionDef(self, node):
        self.scopes.append({})
        self.current_scope = self.scopes[-1]
        self.generic_visit(node)
        node.body = self.insert_awaits(node.body)
        self.scopes.pop()
        self.current_scope = self.scopes[-1]
        return node

    def visit_If(self, node):
        self.scopes.append({})
        self.current_scope = self.scopes[-1]
        self.generic_visit(node)
        node.body = self.insert_awaits(node.body)
        node.orelse = self.insert_awaits(node.orelse)
        self.scopes.pop()
        self.current_scope = self.scopes[-1]
        return node

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'ensure_future':
            if isinstance(node.args[0], ast.Call):
                var_name = self.get_assigned_var(node)
                if var_name:
                    self.current_scope[var_name] = ast.Await(value=node.args[0])
        return node

    def get_assigned_var(self, node):
        parent = self.parent_map.get(node)
        if isinstance(parent, ast.Assign) and len(parent.targets) == 1:
            target = parent.targets[0]
            if isinstance(target, ast.Name):
                return target.id
        return None

    def insert_awaits(self, body):
        new_body = []
        for stmt in body:
            new_body.append(stmt)
            if isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0], ast.Name):
                var_name = stmt.targets[0].id
                if var_name in self.current_scope:
                    new_body.append(ast.Expr(value=self.current_scope[var_name]))
                    del self.current_scope[var_name]
        return new_body

    def visit(self, node):
        self.parent_map = {child: node for child in ast.walk(node) for node in ast.walk(child)}
        return super().visit(node)


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