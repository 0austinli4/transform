import ast
import argparse
import os
from .function_finder import find_functions_with_calls

class FunctionCollector(ast.NodeVisitor):
    def __init__(self):
        self.functions = set()
        self.decorated_functions = set()
    
    def visit_FunctionDef(self, node):
        self.functions.add(node.name)
        if node.decorator_list:
            self.decorated_functions.add(node.name)

class AsyncTransformer(ast.NodeTransformer):
    def __init__(self, functions_calling_async, async_calls):
        self.async_calls = set(async_calls)
        self.transformed_functions = set()
        self.temp_var_counter = 0
        self.future_counter = 0

    def visit_FunctionDef(self, node):
        self.temp_var_counter = 0
        self.future_counter = 0
        if node.name in self.async_calls:
            self.transformed_functions.add(node.name)
            new_body = []
            for stmt in node.body:
                result = self.visit(stmt)
                if isinstance(result, list):
                    new_body.extend(result)
                else:
                    new_body.append(result)

            # Add session_id as the first parameter
            new_args = self.add_session_id_param(node.args)

            return ast.AsyncFunctionDef(
                name=node.name,
                args=new_args,
                body=new_body,
                decorator_list=node.decorator_list,
                returns=node.returns,
                type_comment=node.type_comment
            )
        return self.generic_visit(node)

    def add_session_id_param(self, args):
        """Add session_id as the first parameter to function arguments"""
        # Create a new session_id argument
        session_id_arg = ast.arg(arg='session_id', annotation=None)

        # Create a copy of the args with session_id prepended
        new_args = ast.arguments(
            posonlyargs=args.posonlyargs,
            args=[session_id_arg] + args.args,
            vararg=args.vararg,
            kwonlyargs=args.kwonlyargs,
            kw_defaults=args.kw_defaults,
            kwarg=args.kwarg,
            defaults=args.defaults
        )
        return new_args

    def visit_Call(self, node):
        func_name = self.get_func_name(node)
        if func_name in self.async_calls or any(call in self.async_calls for call in [func_name]):
            return self.transform_async_call(node)
        return node

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            func_name = self.get_func_name(node.value)
            
            if func_name in self.async_calls:
                future_var = f"future_{self.future_counter}"
                self.future_counter += 1
                
                ensure_future_call = self.transform_async_call(node.value)
                future_assign = self.copy_location(ast.Assign(
                    targets=[ast.Name(id=future_var, ctx=ast.Store())],
                    value=ensure_future_call
                ), node)
                
                app_response_assign = self.copy_location(ast.Assign(
                    targets=node.targets,
                    value=ast.Call(
                        func=ast.Name(id='await_request', ctx=ast.Load()),
                        args=[
                            ast.Name(id='session_id', ctx=ast.Load()),
                            ast.Name(id=future_var, ctx=ast.Load())
                        ],
                        keywords=[]
                    )
                ), node)

                return [future_assign, app_response_assign]
        return node

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            func_name = self.get_func_name(node.value)
            if func_name in self.async_calls:
                future_var = f"future_{self.future_counter}"
                self.future_counter += 1

                ensure_future_call = self.transform_async_call(node.value)
                future_assign = self.copy_location(ast.Assign(
                    targets=[ast.Name(id=future_var, ctx=ast.Store())],
                    value=ensure_future_call
                ), node)

                app_response_expr = self.copy_location(ast.Expr(
                    value=ast.Call(
                        func=ast.Name(id='await_request', ctx=ast.Load()),
                        args=[
                            ast.Name(id='session_id', ctx=ast.Load()),
                            ast.Name(id=future_var, ctx=ast.Load())
                        ],
                        keywords=[]
                    )
                ), node)

                return [future_assign, app_response_expr]
        return node

    def visit_If(self, node):
        transformed_test, assignments = self.transform_condition(node.test)
        if assignments:
            new_if = self.copy_location(ast.If(
                test=transformed_test,
                body=[self.visit(stmt) for stmt in node.body],
                orelse=[self.visit(stmt) for stmt in node.orelse]
            ), node)
            return assignments + [new_if]
        else:
            node.test = self.visit(node.test)
            node.body = [self.visit(stmt) for stmt in node.body]
            node.orelse = [self.visit(stmt) for stmt in node.orelse]
            return node
    
    def visit_While(self, node):
        transformed_test, assignments = self.transform_condition(node.test)
        if assignments:
            new_while = self.copy_location(ast.While(
                test=transformed_test,
                body=[self.visit(stmt) for stmt in node.body],
                orelse=[self.visit(stmt) for stmt in node.orelse]
            ), node)
            return assignments + [new_while]
        else:
            node.test = self.visit(node.test)
            node.body = [self.visit(stmt) for stmt in node.body]
            node.orelse = [self.visit(stmt) for stmt in node.orelse]
            return node

    def visit_For(self, node):
        if isinstance(node.iter, ast.Call) and self.is_async_call(node.iter):
            future_var = f"future_{self.future_counter}"
            iter_var = f"async_iter_{self.temp_var_counter}"
            self.future_counter += 1
            self.temp_var_counter += 1

            future_assign = self.copy_location(ast.Assign(
                targets=[ast.Name(id=future_var, ctx=ast.Store())],
                value=self.transform_async_call(node.iter)
            ), node)

            app_response_assign = self.copy_location(ast.Assign(
                targets=[ast.Name(id=iter_var, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id='await_request', ctx=ast.Load()),
                    args=[
                        ast.Name(id='session_id', ctx=ast.Load()),
                        ast.Name(id=future_var, ctx=ast.Load())
                    ],
                    keywords=[]
                )
            ), node)

            new_for = self.copy_location(ast.For(
                target=node.target,
                iter=ast.Name(id=iter_var, ctx=ast.Load()),
                body=[self.visit(stmt) for stmt in node.body],
                orelse=[self.visit(stmt) for stmt in node.orelse]
            ), node)

            return [future_assign, app_response_assign, new_for]
        else:
            node.iter = self.visit(node.iter)
            node.body = [self.visit(stmt) for stmt in node.body]
            node.orelse = [self.visit(stmt) for stmt in node.orelse]
            return node

    def transform_iterable(self, node):
        if isinstance(node, ast.Call) and self.is_async_call(node):
            iter_var = f"async_iter_{self.temp_var_counter}"
            self.temp_var_counter += 1

            iter_assign = self.copy_location(ast.Assign(
                targets=[ast.Name(id=iter_var, ctx=ast.Store())],
                value=self.transform_async_call(node)
            ), node)

            app_response_expr = self.copy_location(ast.Expr(
                value=ast.Call(
                    func=ast.Name(id='await_request', ctx=ast.Load()),
                    args=[
                        ast.Name(id='session_id', ctx=ast.Load()),
                        ast.Name(id=iter_var, ctx=ast.Load())
                    ],
                    keywords=[]
                )
            ), node)

            return ast.Name(id=iter_var, ctx=ast.Load()), [iter_assign, app_response_expr]
        return node, []

    def transform_condition(self, node):
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            transformed_operand, assignments = self.transform_condition(node.operand)
            return ast.UnaryOp(op=ast.Not(), operand=transformed_operand), assignments
        elif isinstance(node, ast.Call) and self.is_async_call(node):
            future_var = f"future_{self.future_counter}"
            cond_var = f"async_cond_{self.temp_var_counter}"
            self.future_counter += 1
            self.temp_var_counter += 1

            future_assign = self.copy_location(ast.Assign(
                targets=[ast.Name(id=future_var, ctx=ast.Store())],
                value=self.transform_async_call(node)
            ), node)

            app_response_assign = self.copy_location(ast.Assign(
                targets=[ast.Name(id=cond_var, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id='await_request', ctx=ast.Load()),
                    args=[
                        ast.Name(id='session_id', ctx=ast.Load()),
                        ast.Name(id=future_var, ctx=ast.Load())
                    ],
                    keywords=[]
                )
            ), node)

            return ast.Name(id=cond_var, ctx=ast.Load()), [future_assign, app_response_assign]
        return node, []

    def is_async_call(self, node):
        return isinstance(node, ast.Call) and self.get_func_name(node) in self.async_calls

    def get_func_name(self, node):
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return None

    def transform_async_call(self, node):
        func_name = self.get_func_name(node)

        ## this is modifiable - r can be whatever the user has set redis to
        if func_name and func_name.startswith('r.'):
            # Extract the Redis operation (after 'r.')
            redis_op = func_name.split('.')[-1].upper()

            # Build arguments for send_request(session_id, operation, key, new_val="", old_val="")
            args = [
                ast.Name(id='session_id', ctx=ast.Load()),
                ast.Constant(value=redis_op),
            ]

            # Add key (first argument from original call)
            if node.args:
                args.append(node.args[0])
            else:
                args.append(ast.Constant(value=""))

            # Add new_val (second argument from original call, if present)
            if len(node.args) > 1:
                args.append(node.args[1])

            # Add old_val (third argument from original call, if present)
            if len(node.args) > 2:
                args.append(node.args[2])

            # Create send_request call
            return ast.Call(
                func=ast.Name(id='send_request', ctx=ast.Load()),
                args=args,
                keywords=[]
            )

        # Default to ensure_future for non-Redis calls
        raise ValueError(f"Cannot use send_request with non-Redis call: {func_name}. "
        "This method is not marked for async transformation.")
    
    def copy_location(self, new_node, old_node):
        ast.copy_location(new_node, old_node)
        ast.fix_missing_locations(new_node)
        return new_node

def collect_top_level_functions(source_code):
    tree = ast.parse(source_code)
    collector = FunctionCollector()
    collector.visit(tree)
    return list(collector.decorated_functions)


def async_form(source_code, functions_calling_async, async_calls):
    external_function_calls = collect_top_level_functions(source_code)
    
    tree = ast.parse(source_code)
    
    # Add asyncio import
    transformer = AsyncTransformer(functions_calling_async, async_calls)
    transformed_tree = transformer.visit(tree)

    ast.fix_missing_locations(transformed_tree)
        
    new_source_code = ast.unparse(transformed_tree)
    return new_source_code, external_function_calls

def main():
    parser = argparse.ArgumentParser(description="Transform 'get' and 'set' calls into async 'await' calls.")
    parser.add_argument('input_files', nargs='+', help="The Python file(s) to transform")
    parser.add_argument('methods', help="Comma-separated list of methods to transform")

    args = parser.parse_args()
    async_calls = [method.strip() for method in args.methods.split(',')]
    output_dir = os.path.join('output')
    os.makedirs(output_dir, exist_ok=True)


    for input_file in args.input_files:
        with open(input_file, 'r') as f:
            source_code = f.read()
    
        tree = ast.parse(source_code)

        transformer = AsyncTransformer(async_calls)
        transformed_tree = transformer.visit(tree)

        ast.fix_missing_locations(transformed_tree)
        
        new_source_code = ast.unparse(transformed_tree)

        output_file = input_file.replace('.py', '_async.py')
        output_file_path = os.path.join(output_dir, os.path.basename(output_file))
        
        with open(output_file_path, 'w') as f:
            f.write(new_source_code)

if __name__ == "__main__":
    main()