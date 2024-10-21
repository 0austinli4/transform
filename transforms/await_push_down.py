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
        # Only add names that are in a "load" context (i.e., being used, not assigned)
        if isinstance(node.ctx, ast.Load):
            self.variables.add(node.id)
    
    def visit_If(self, node):
        # Visit the test condition of the if statement
        self.visit(node.test)
        # Visit the body and orelse parts
        for stmt in node.body + node.orelse:
            self.visit(stmt)

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
        self.var_dependencies = {}
        self.awaits = {}
        self.awaits_stack = [{}]  # Stack of await dictionaries
    
    def visit_AsyncFunctionDef(self, node):
        print(f"Visiting AsyncFunctionDef: {node.name}")
        self.var_dependencies.clear()
        self.awaits.clear()
        self.awaits_stack = [{}]
        node.body = self.process_body(node.body)
        return node
    
    def process_body(self, body):
        print("PROCESSING BODY")
        temp_body = []
        final_body = []
        
        for stmt in body:
            print(f"Processing statement: {ast.dump(stmt)[:50]}...")
            self.awaits_stack.append({})
            stmt = self.visit(stmt)
            current_awaits = self.awaits_stack.pop()
            self.awaits_stack[-1].update(current_awaits)

            variables_used = get_variables_used(stmt)

            if self.is_await_call(stmt):
                print("Encountered await call")
                await_variable_name = self.get_await_variable_name(stmt)
                print(f"Added await: {await_variable_name}")
                self.awaits_stack[-1][await_variable_name] = stmt
            elif isinstance(stmt, ast.If):
                print("Encountered If statement in process_body")
                # If we encounter an If statement, process everything collected so far
                final_body.extend(temp_body)
                final_body.append(stmt)
                # final_body.extend(self.awaits.values())
                # self.awaits.clear()
                # Then add the If statement as is
                temp_body = []
            elif variables_used.intersection(self.awaits_stack[-1].keys()):
                print(f"Variables used: {variables_used}")
                final_body.extend(temp_body)
                variables_remove = variables_used.intersection(self.awaits_stack[-1].keys())
                for variable_name in variables_remove:
                    # print("POPPING OUT AWAIT STATEMENT ", variable_name)
                    final_body.append(self.awaits_stack[-1][variable_name])
                    del self.awaits_stack[-1][variable_name] 
                final_body.append(stmt)
                temp_body = []
            elif self.is_external_function_call(stmt):
                print("Encountered external function call or return statement")
                # If we hit an external function call, process collected calls
                final_body.extend(temp_body)
                final_body.extend(self.awaits_stack[-1].values())
                self.awaits_stack[-1].clear()
                final_body.append(stmt)
                temp_body = []
            elif self.is_return_statement(stmt):
                print("At the last line")
                final_body.extend(temp_body)
                final_body.extend(self.awaits_stack[-1].values())
                self.awaits_stack[-1].clear()
                final_body.append(stmt)
                temp_body = []
            else:
                stmt = self.visit(stmt)
                temp_body.append(self.visit(stmt))
        # Combine the processed statements
        print("Finalizing process_body")
        final_body.extend(temp_body)
        final_body.extend(self.awaits_stack[-1].values())
        self.awaits_stack[-1].clear()
        # final_body.extend(temp_body)
        # final_body.extend(self.awaits.values())
        # self.awaits = dict()

        return final_body

    def get_await_variable_name(self, stmt):
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Await):
            if isinstance(stmt.targets[0], ast.Name):
                return stmt.targets[0].id
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Await):
            if isinstance(stmt.value.value, ast.Name):
                return stmt.value.value.id
        return None
    # def visit_Call(self, node):
    #     args = self.get_all_arguments(node)
    #     for arg in args:
    #         if isinstance(arg, ast.Name):
    #             self.var_dependencies.setdefault(arg.id, set()).add(self.get_call_name(node))
    #     return node

    # def get_call_name(self, node):
    #     if isinstance(node.func, ast.Name):
    #         return node.func.id
    #     elif isinstance(node.func, ast.Attribute):
    #         return node.func.attr
    #     return ''

    # def get_all_arguments(self, node):
    #     args = []
    #     if isinstance(node, ast.Call):
    #         args.extend(node.args)
    #         args.extend([kw.value for kw in node.keywords])
    #         if isinstance(node.func, ast.Attribute):
    #             args.append(node.func.value)
    #     return args


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

    # def visit_AsyncFunctionDef(self, node):
    #     self.scopes.append({})
    #     self.current_scope = self.scopes[-1]
    #     self.generic_visit(node)
    #     node.body = self.insert_awaits(node.body)
    #     self.scopes.pop()
    #     self.current_scope = self.scopes[-1]
    #     return node

    def visit_If(self, node):
        node.body = self.process_body(node.body)
        if node.orelse:
            if isinstance(node.orelse[0], ast.If):
                node.orelse = [self.visit(node.orelse[0])]
            else:
                node.orelse = self.process_body(node.orelse)
        # node.orelse = self.process_body(node.orelse)
        return node


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
