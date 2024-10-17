import ast
import argparse
import os
from .await_push_down import get_variables_used

class AssignmentTargetCollector(ast.NodeVisitor):
    def __init__(self):
        self.targets = set()

    def visit_Assign(self, node):
        for target in node.targets:
            self.visit(target)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.targets.add(node.id)

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Store):
            if isinstance(node.value, ast.Name):
                self.targets.add(f"{node.value.id}.{node.attr}")
        self.visit(node.value)

    def visit_Tuple(self, node):
        for elt in node.elts:
            self.visit(elt)

    def visit_List(self, node):
        for elt in node.elts:
            self.visit(elt)

def get_assignment_targets(stmt):
    collector = AssignmentTargetCollector()
    collector.visit(stmt)
    return set(collector.targets)

class AsyncFuturePushUp(ast.NodeTransformer):
    def __init__(self, external_functions):
        self.external_functions = external_functions

    def visit_AsyncFunctionDef(self, node):
        node.body = self.process_body(node.body)
        return node

    def process_body(self, body):
        future_calls = []
        temp_body = []
        final_body = []
        vars_produced = set()

        for stmt in body:
            if self.is_ensure_future_call(stmt):
                variables_used = get_variables_used(stmt)
                print("\n\nVARIABLES PRODUCED", vars_produced)
                print("\n\nVARIABLES USED", variables_used)

                if variables_used.intersection(vars_produced):
                    print("EXTENSIONS" , stmt)
                    temp_body.extend(future_calls)

                    temp_body = self.process_deps(temp_body, stmt)
                    final_body.extend(temp_body)
                    temp_body = []
                    vars_produced = set()
                else:
                    future_calls.append(stmt)
            elif self.is_await_call(stmt):
                future_calls.append(stmt)
            elif self.is_external_function_call(stmt):
                # If we hit an external function call, process collected calls
                final_body.extend(future_calls)
                final_body.extend(temp_body)
                final_body.append(stmt)
                future_calls = []
                temp_body = []
            else:
                targets = get_assignment_targets(stmt)
                vars_produced.update(targets)
                temp_body.append(self.visit(stmt))
            
        # Combine the processed statements
        # processed_body = ensure_future_calls + other_statements
        final_body.extend(future_calls)
        final_body.extend(temp_body)
        # Add the return statement if it exists
        # if return_stmt:
        #     processed_body.append(return_stmt)
        return final_body
    
    def process_deps(self, temp_body, stmt):
        print("PROCESSING DEP", stmt)
        targets = get_variables_used(stmt)
        
        for i, temp_stmt in enumerate(temp_body):
            vars_produced = get_assignment_targets(temp_stmt)
            if vars_produced.intersection(targets):
                temp_body.insert(i+1, stmt)
                return temp_body
        
        # If no insertion point found, append the statement to the end
        temp_body.append(stmt)
        return temp_body

    def is_ensure_future_call(self, node):
        return (isinstance(node, ast.Assign) and
                isinstance(node.value, ast.Call) and
                isinstance(node.value.func, ast.Attribute) and
                node.value.func.attr == 'ensure_future')

    def is_external_function_call(self, node):
        return (isinstance(node, ast.Expr) and
                isinstance(node.value, ast.Call) and
                isinstance(node.value.func, ast.Name) and
                node.value.func.id in self.external_functions)

    def is_await_call(self, node):
        return (isinstance(node, ast.Expr) and
                isinstance(node.value, ast.Await))
    
    # def visit_If(self, node):
    #     node.body = self.process_body(node.body)
    #     if node.orelse:
    #         if isinstance(node.orelse[0], ast.If):
    #             node.orelse = [self.visit(node.orelse[0])]
    #         else:
    #             node.orelse = self.process_body(node.orelse)
    #     # node.orelse = self.process_body(node.orelse)
    #     return node

    # def visit_For(self, node):
    #     node.body = self.process_body(node.body)
    #     node.orelse = self.process_body(node.orelse)
    #     return node

    # def visit_While(self, node):
    #     node.body = self.process_body(node.body)
    #     node.orelse = self.process_body(node.orelse)
    #     return node

def async_future(source_code, external_functions):
    print("hello running")
    tree = ast.parse(source_code)
    transformer = AsyncFuturePushUp(external_functions)
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    new_source_code = ast.unparse(transformed_tree)
    return new_source_code
