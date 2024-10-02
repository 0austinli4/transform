import ast
import argparse
import os

class AwaitMover(ast.NodeTransformer):
    def __init__(self):
        self.future_calls = {}
        self.used_variables = set()

    def visit_Await(self, node):
        if isinstance(node.value, ast.Name):
            self.future_calls[node.value.id] = node
        return ast.Pass()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'ensure_future':
            if isinstance(node.args[0], ast.Call):
                var_name = self.get_assigned_var(node)
                if var_name:
                    self.future_calls[var_name] = ast.Await(value=node.args[0])
                return node.args[0]
        else:
            # Check all arguments of any function call
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    self.used_variables.add(arg.id)
            # Also check keyword arguments
            for keyword in node.keywords:
                if isinstance(keyword.value, ast.Name):
                    self.used_variables.add(keyword.value.id)
        return node

    def visit_Name(self, node):
        # Track all variable uses, not just in function calls
        if isinstance(node.ctx, ast.Load):
            self.used_variables.add(node.id)
        return node

    def get_assigned_var(self, node):
        parent = self.parent_map.get(node)
        if isinstance(parent, ast.Assign) and len(parent.targets) == 1:
            target = parent.targets[0]
            if isinstance(target, ast.Name):
                return target.id
        return None

    def visit_AsyncFunctionDef(self, node):
        self.parent_map = {child: node for child in ast.walk(node) for node in ast.walk(child)}
        self.future_calls.clear()
        self.used_variables.clear()

        new_body = []
        for stmt in node.body:
            new_stmt = self.visit(stmt)
            awaits_to_insert = []
            self.collect_awaits(new_stmt, awaits_to_insert)
            new_body.extend(awaits_to_insert)
            new_body.append(new_stmt)

        # append the remaining awaits to the end of the function
        for var, await_node in self.future_calls.items():
            if var not in self.used_variables:
                new_body.append(ast.Expr(value=await_node))

        node.body = new_body
        return node

    def collect_awaits(self, node, awaits):
        if isinstance(node, ast.Name) and node.id in self.future_calls:
            awaits.append(ast.Expr(value=self.future_calls[node.id]))
            del self.future_calls[node.id]
        elif isinstance(node, ast.AST):
            for child in ast.iter_child_nodes(node):
                self.collect_awaits(child, awaits)

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