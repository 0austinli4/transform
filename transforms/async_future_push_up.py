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
        docstring = ast.get_docstring(node)
        if docstring:
            node.body = [ast.Expr(ast.Str(s=docstring))] + self.process_body(node.body)
        else:
            node.body = self.process_body(node.body)
        return node
    
    def visit_If(self, node):
        node.body = self.process_body(node.body)
        if node.orelse:
            if isinstance(node.orelse[0], ast.If):
                node.orelse = [self.visit(node.orelse[0])]
            else:
                node.orelse = self.process_body(node.orelse)
        return node

    def process_body(self, body):
        future_calls = []
        temp_body = []
        final_body = []
        vars_produced = set()

        for stmt in body:
            stmt = self.visit(stmt)
            if self.is_app_request_call(stmt):
                variables_used = get_variables_used(stmt)
                

                new_body = []

                if variables_used.intersection(vars_produced):
                    temp_body = future_calls + temp_body
                    temp_body = self.process_deps(temp_body, stmt)
                    final_body.extend(temp_body)
                    temp_body = []
                    vars_produced = set()
                    future_calls = []
                else:
                    future_calls.append(stmt)
            elif self.is_app_response_call(stmt):
                targets = get_assignment_targets(stmt)
                vars_produced.update(targets)
                future_calls.append(stmt)
            elif self.is_external_function_call(stmt):
                # If we hit an external function call, process collected calls
                final_body.extend(future_calls)
                final_body.extend(temp_body)
                final_body.append(stmt)
                future_calls = []
                temp_body = []
                vars_produced = set()
            else:
                targets = get_assignment_targets(stmt)
                vars_produced.update(targets)
                temp_body.append(stmt)
        # Combine the processed statements
        # processed_body = ensure_future_calls + other_statements
        final_body.extend(future_calls)
        final_body.extend(temp_body)
        # Add the return statement if it exists
        return final_body
    
    def process_deps(self, temp_body, stmt):
        targets = get_variables_used(stmt)
        latest_insertion_point = -1
        
        for i, temp_stmt in enumerate(temp_body):
            vars_produced = get_assignment_targets(temp_stmt)
            if vars_produced.intersection(targets):
                latest_insertion_point = i+1
    
        if latest_insertion_point != -1:
            temp_body.insert(latest_insertion_point, stmt)
        else:
            raise Exception('no insertion point found')
        return temp_body  
        # # If no insertion point found, append the statement to the end
        # temp_body.append(stmt)
        # return temp_body

    def is_ensure_future_call(self, node):
        return (isinstance(node, ast.Assign) and
                isinstance(node.value, ast.Call) and
                isinstance(node.value.func, ast.Attribute) and
                node.value.func.attr == 'ensure_future')

    def is_app_response_call(self, node):
        # Check for expression statements
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                return node.value.func.id == 'AppResponse'
        # Check for assignments where the value is an AppResponse call
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                return node.value.func.id == 'AppResponse'
        return False

    def is_app_request_call(self, node):
        # Check for expression statements
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                return node.value.func.id == 'AppRequest'
        # Check for assignments where the value is an AppRequest call
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                return node.value.func.id == 'AppRequest'
        return False

    def is_external_function_call(self, node):
        return (isinstance(node, ast.Expr) and
                isinstance(node.value, ast.Call) and
                isinstance(node.value.func, ast.Name) and
                node.value.func.id in self.external_functions)

    def is_await_call(self, node):
        return (isinstance(node, (ast.Expr, ast.Assign)) and
                isinstance(getattr(node, 'value', None), ast.Await))
        
    
    # def visit_For(self, node):
    #     node.body = self.process_body(node.body)
    #     node.orelse = self.process_body(node.orelse)
    #     return node

    # def visit_While(self, node):
    #     node.body = self.process_body(node.body)
    #     node.orelse = self.process_body(node.orelse)
    #     return node

def async_future(source_code, external_functions):
    tree = ast.parse(source_code)
    transformer = AsyncFuturePushUp(external_functions)
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    new_source_code = ast.unparse(transformed_tree)
    return new_source_code
