import ast
import argparse
import os

class AsyncTransformer(ast.NodeTransformer):
    def __init__(self):
        self.ensure_future_vars = []
    
    def visit_Import(self, node):
        """
        Change the import statement to use api_async (hardcoded)
        """
        new_names = [ast.alias(name='asyncio')]
        for alias in node.names:
            if alias.name == 'api':
                new_names.append(ast.alias(name='api_async', asname=alias.asname))
            else:
                new_names.append(alias)
        return ast.Import(names=new_names)

    def visit_ImportFrom(self, node):
        """
        api -> api_async naming
        """
        if node.module == 'api':
            return ast.ImportFrom(module='api_async', names=node.names, level=node.level)
        return node

    def visit_ClassDef(self, node):
        """
        Visit each function definition
        """
        for i, body_item in enumerate(node.body):
            if isinstance(body_item, ast.FunctionDef):
                node.body[i] = self.visit_FunctionDef(body_item)
        return node

    def visit_FunctionDef(self, node):
        """
        Add "async" to any function definitions in the program
        """
        # Get all lines in the function
        new_body = [self.visit(stmt) for stmt in node.body]
        
        async_node = ast.AsyncFunctionDef(
            name=node.name,
            args=node.args,
            body=new_body,
            decorator_list=node.decorator_list,
            returns=node.returns,
            type_comment=node.type_comment
        )
        
        return async_node
    
    def visit_Call(self, node):
        """
        For any function calls like api.set(42), transform them into 
        asyncio.ensure_future(api.set(42)) and add await to get the result 
        on the next line.
        """
        # Visit child nodes (important for visiting nested expressions)
        node = self.generic_visit(node)

        # Check if the expression is a function call (ast.Call)
        if isinstance(node.func, ast.Attribute) and node.func.attr in ['get_name', 'make_post', 'set_profile_picture']:
            # Create the asyncio.ensure_future call
            ensure_future_call = ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='asyncio', ctx=ast.Load()),  # asyncio.ensure_future
                    attr='ensure_future',
                    ctx=ast.Load()
                ),
                args=[node],  # Pass the original function call as an argument
                keywords=[]  # No keyword arguments
            )

            return ensure_future_call

        return node

    def visit_Assign(self, node):
        node = self.generic_visit(node)
        
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
            # Check if the function is ensure_future
            if (node.value.func.attr == 'ensure_future' and
                isinstance(node.value.func.value, ast.Name) and
                node.value.func.value.id == 'asyncio'):
                
                # Get the variable name being assigned to (left-hand side)
                assigned_var = node.targets[0]

                if isinstance(assigned_var, ast.Name):
                    self.ensure_future_vars.append(assigned_var.id)

                    # Create the await object
                    await_object = ast.Await(
                        value=ast.Name(id=assigned_var.id, ctx=ast.Load())
                    )

                    # Create a new line with the await expression
                    await_stmt = ast.Expr(value=await_object)

                    # Return a list of nodes: the original assignment and the new await statement
                    return [node, await_stmt]

        return node

    def visit_Expr(self, node):
        """
        For any function calls that include get and set, make sure the functions they exist in 
        change to async 
        """
        node = self.generic_visit(node)
        if isinstance(node.value, ast.Call):
            # If it's a call to an async function, make sure it's awaited
            if isinstance(node.value.func, ast.Name) and node.value.func.id in ['run', 'my_function']:
                return ast.Expr(value=ast.Await(value=node.value))
        return node

def main():
    # Set up argparse to handle command line arguments for multiple input files
    parser = argparse.ArgumentParser(description="Transform 'get' and 'set' calls into async 'await' calls.")
    parser.add_argument('input_files', nargs='+', help="The Python file(s) to transform")
    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = os.path.join('..', 'output')
    os.makedirs(output_dir, exist_ok=True)

    for input_file in args.input_files:
        with open(input_file, 'r') as f:
            source_code = f.read()

        tree = ast.parse(source_code)

        transformer = AsyncTransformer()
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