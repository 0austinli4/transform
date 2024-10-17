import ast
import argparse
import os

class FunctionCollector(ast.NodeVisitor):
    def __init__(self):
        self.functions = set()
        self.decorated_functions = set()
    
    def visit_FunctionDef(self, node):
        self.functions.add(node.name)
        if node.decorator_list:
            self.decorated_functions.add(node.name)

class AsyncTransformer(ast.NodeTransformer):
    def __init__(self, async_calls):
        self.async_calls = set(async_calls)
        self.transformed_functions = set()
        self.temp_var_counter = 0

    def visit_FunctionDef(self, node):
        if node.name in self.async_calls:
            self.transformed_functions.add(node.name)
            new_body = []
            for stmt in node.body:
                result = self.visit(stmt)
                if isinstance(result, list):
                    new_body.extend(result)
                else:
                    new_body.append(result)
            return ast.AsyncFunctionDef(
                name=node.name,
                args=node.args,
                body=new_body,
                decorator_list=node.decorator_list,
                returns=node.returns,
                type_comment=node.type_comment
            )
        return self.generic_visit(node)

    def visit_Call(self, node):
        func_name = self.get_func_name(node)
        if func_name in self.async_calls:
            return self.transform_async_call(node)
        return node

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            func_name = self.get_func_name(node.value)
            if func_name in self.async_calls:
                ensure_future_call = self.transform_async_call(node.value)
                assign = self.copy_location(ast.Assign(targets=node.targets, value=ensure_future_call), node)
                await_expr = self.copy_location(ast.Expr(
                    value=ast.Await(value=ast.Name(id=node.targets[0].id, ctx=ast.Load()))
                ), node)
                return [assign, await_expr]
        return node

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            func_name = self.get_func_name(node.value)
            if func_name in self.async_calls:
                var_name = f"async_{func_name}_{self.temp_var_counter}"
                self.temp_var_counter += 1
                ensure_future_call = self.transform_async_call(node.value)
                assign = self.copy_location(ast.Assign(
                    targets=[ast.Name(id=var_name, ctx=ast.Store())],
                    value=ensure_future_call
                ), node)
                await_expr = self.copy_location(ast.Expr(
                    value=ast.Await(value=ast.Name(id=var_name, ctx=ast.Load()))
                ), node)
                return [assign, await_expr]
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
                body=[self.visit(stmt) for stmt in node.body] + assignments,
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
            var_name = f"async_iter_{self.temp_var_counter}"
            self.temp_var_counter += 1
            assign = self.copy_location(ast.Assign(
                targets=[ast.Name(id=var_name, ctx=ast.Store())],
                value=self.transform_async_call(node.iter)
            ), node)
            await_expr = self.copy_location(ast.Expr(
                value=ast.Await(value=ast.Name(id=var_name, ctx=ast.Load()))
            ), node)
            new_for = self.copy_location(ast.For(
                target=node.target,
                iter=ast.Name(id=var_name, ctx=ast.Load()),
                body=[self.visit(stmt) for stmt in node.body],
                orelse=[self.visit(stmt) for stmt in node.orelse]
            ), node)
            return [assign, await_expr, new_for]
        else:
            node.iter = self.visit(node.iter)
            node.body = [self.visit(stmt) for stmt in node.body]
            node.orelse = [self.visit(stmt) for stmt in node.orelse]
            return node

    def transform_condition(self, node):
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            transformed_operand, assignments = self.transform_condition(node.operand)
            return ast.UnaryOp(op=ast.Not(), operand=transformed_operand), assignments
        elif isinstance(node, ast.Call) and self.is_async_call(node):
            var_name = f"async_cond_{self.temp_var_counter}"
            self.temp_var_counter += 1
            assign = self.copy_location(ast.Assign(
                targets=[ast.Name(id=var_name, ctx=ast.Store())],
                value=self.transform_async_call(node)
            ), node)
            await_expr = self.copy_location(ast.Expr(
                value=ast.Await(value=ast.Name(id=var_name, ctx=ast.Load()))
            ), node)
            return ast.Name(id=var_name, ctx=ast.Load()), [assign, await_expr]
        return node, []

    def is_async_call(self, node):
        return isinstance(node, ast.Call) and self.get_func_name(node) in self.async_calls

    def get_func_name(self, node):
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def transform_async_call(self, node):
        return ast.Call(
            func=ast.Attribute(
                value=ast.Name(id='asyncio', ctx=ast.Load()),
                attr='ensure_future',
                ctx=ast.Load()
            ),
            args=[node],
            keywords=[]
        )

    def copy_location(self, new_node, old_node):
        ast.copy_location(new_node, old_node)
        ast.fix_missing_locations(new_node)
        return new_node

def collect_top_level_functions(source_code):
    tree = ast.parse(source_code)
    collector = FunctionCollector()
    collector.visit(tree)
    # print("List of decorated functions", list(collector.decorated_functions))
    return list(collector.decorated_functions)


def async_form(source_code, async_calls):
    external_function_calls = collect_top_level_functions(source_code)

    tree = ast.parse(source_code)
    
    # Add asyncio import
    asyncio_import = ast.Import(names=[ast.alias(name='asyncio', asname=None)])
    tree.body.insert(0, asyncio_import)

    transformer = AsyncTransformer(async_calls)
    transformed_tree = transformer.visit(tree)

    ast.fix_missing_locations(transformed_tree)
        
    new_source_code = ast.unparse(transformed_tree)
    return new_source_code, external_function_calls

def main():
    # Set up argparse to handle command line arguments for multiple input files
    parser = argparse.ArgumentParser(description="Transform 'get' and 'set' calls into async 'await' calls.")
    parser.add_argument('input_files', nargs='+', help="The Python file(s) to transform")
    parser.add_argument('methods', help="Comma-separated list of methods to transform")

    args = parser.parse_args()
    async_calls = [method.strip() for method in args.methods.split(',')]
    print("ALL ASYNC CALLS INPUT", async_calls)
    # Ensure output directory exists
    output_dir = os.path.join('output')
    os.makedirs(output_dir, exist_ok=True)

    for input_file in args.input_files:
        # Collect top-level functions
        collect_top_level_functions(input_file)
        print(f"Top-level functions from {input_file}:")
        print(", ".join(async_calls))
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

        print(f"Transformed code has been written to {output_file_path}.")
        
        # Print the collected variables
        print("Variables assigned to asyncio.ensure_future calls:")
        print(", ".join(transformer.ensure_future_vars))

if __name__ == "__main__":
    main()
