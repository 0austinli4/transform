import ast
import argparse
import os
from collections import deque

class VariableCollector(ast.NodeVisitor):
    def __init__(self):
        self.variables = set()

    def visit_Call(self, node):
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
        print("\n\nStart of push down class")
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
        print("\n\nDepth ", self.nesting, "Local awaits ", local_awaits)
        print("Starting process body ", self.all_awaits)

        temp_body = []
        final_body = []
        
        for stmt in body:
            stmt = self.visit(stmt)
            variables_used = get_variables_used(stmt)

            print("VARIABLES USED AT THIS LINE", variables_used)

            if self.is_await_call(stmt):

                print("existing all awaits", self.all_awaits)
                self.all_awaits.add(stmt)
                print("updating self.all_awaits", self.all_awaits)

                await_variable_name = self.get_await_variable_name(stmt)
                print("Found await call", await_variable_name, stmt)
                self.var_dependencies[await_variable_name] = stmt

                current_awaits.add(stmt)

                local_awaits.add(stmt)

            elif variables_used.intersection(self.var_dependencies.keys()):
                # dependency is found
                print("Dependency is found")
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
                print("all awaits after doing removal", self.all_awaits)
                temp_body = []

                if self.is_return_statement(stmt):
                    print("return dependent line")
                    print("Dump awaits - return", current_awaits)
                    final_body.extend(temp_body)

                    # dump current awaits
                    awaits_to_add = list(current_awaits)
                    final_body.extend(awaits_to_add)

                    # if main execution level, this is last return
                    if self.nesting == 1:
                        print("Dependent reutrn ")
                        self.var_dependencies.clear()
                        self.all_awaits = set()
                    
                    current_awaits = set()
                    local_awaits = set()
                    temp_body = []

                final_body.append(stmt)
            elif self.is_return_statement(stmt) or self.is_external_function_call(stmt):
                print("This is a return statement")
                print("Dump awaits - return", current_awaits)
                final_body.extend(temp_body)

                awaits_to_add = list(current_awaits)
                final_body.extend(awaits_to_add)
                final_body.append(stmt)

                if self.nesting == 1:
                    print("clearing all")
                    self.var_dependencies.clear()
                    self.all_awaits = set()
                current_awaits = set()
                local_awaits = set()
                temp_body = []
            else:
                temp_body.append(stmt)
        # Combine the processed statements
        final_body.extend(temp_body)

        print("Finished local, dumping awaits", local_awaits)
        final_body.extend(local_awaits)
        # update await
        print("self.all_awaits ", self.all_awaits)
        for awt in local_awaits:
            print("discarding", awt)
            print("COMPARE",awt,self.all_awaits)
            self.all_awaits.discard(awt)
            current_awaits.discard(awt)

            await_variable_name = self.get_await_variable_name(awt)
            del self.var_dependencies[await_variable_name]
        print("status of all awaits", self.all_awaits)
        local_awaits = set()

        if self.nesting == 1:
            print("nesting is 1, clearing all")
            final_body.extend(current_awaits)
            self.var_dependencies.clear()
            self.all_awaits = set()

        self.nesting -= 1
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
