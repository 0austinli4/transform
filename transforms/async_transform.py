import ast
import argparse
import os

async_calls = []

class FunctionCollector(ast.NodeVisitor):
    def __init__(self):
        self.functions = set()
    
    def visit_FunctionDef(self, node):
        self.functions.add(node.name)

class AsyncTransformer(ast.NodeTransformer):
    def __init__(self, async_calls):
        self.ensure_future_vars = []
        self.async_calls = async_calls
        self.transformed_functions = set()  # Add this line
        self.parent_node = None
        print("ALL ASYNC CALLS", async_calls)
    
    def visit(self, node):
        old_parent = self.parent_node
        self.parent_node = node
        result = super().visit(node)
        self.parent_node = old_parent
        return result
    
    def visit_If(self, node):
        if isinstance(node.test, ast.Call):
            var_name = f"async_var_{len(self.ensure_future_vars)}"
            
            assign = self.copy_location(ast.Assign(
                targets=[ast.Name(id=var_name, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id='asyncio', ctx=ast.Load()),
                        attr='ensure_future',
                        ctx=ast.Load()
                    ),
                    args=[node.test],
                    keywords=[]
                )
            ), node)
            
            await_stmt = self.copy_location(ast.Expr(
                value=ast.Await(
                    value=ast.Name(id=var_name, ctx=ast.Load())
                )
            ), node)
            
            node.test = ast.Name(id=var_name, ctx=ast.Load())
            
            node.body = [self.visit(stmt) for stmt in node.body]
            node.orelse = [self.visit(stmt) for stmt in node.orelse]
            
            return [assign, await_stmt, node]
        else:
            return self.generic_visit(node)

    # def visit_Import(self, node):
    #     """
    #     Change the import statement to use api_async (hardcoded)
    #     """
    #     new_names = [ast.alias(name='asyncio')]
    #     for alias in node.names:
    #         if alias.name == 'api':
    #             new_names.append(ast.alias(name='api_async', asname=alias.asname))
    #         else:
    #             new_names.append(alias)
    #     return ast.Import(names=new_names)

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
        new_body = [self.visit(stmt) for stmt in node.body]
        self.transformed_functions.add(node.name)
        
        async_node = self.copy_location(ast.AsyncFunctionDef(
            name=node.name,
            args=node.args,
            body=new_body,
            decorator_list=node.decorator_list,
            returns=node.returns,
            type_comment=node.type_comment
        ), node)
        
        return async_node


    def visit_Call(self, node):
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Attribute) and node.func.attr != "__init__" and node.func.attr in self.async_calls or \
        (isinstance(node.func, ast.Name) and node.func.id in self.transformed_functions):
            if not isinstance(self.parent_node, ast.If):
                    ensure_future_call = self.copy_location(ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='asyncio', ctx=ast.Load()),
                            attr='ensure_future',
                            ctx=ast.Load()
                        ),
                        args=[node],
                        keywords=[]  
                    ), node)
                    return ensure_future_call
        return node

    def copy_location(self, new_node, old_node):
        ast.copy_location(new_node, old_node)
        ast.fix_missing_locations(new_node)
        return new_node


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

    # def visit_Expr(self, node):
    #     """
    #     For any function calls that include get and set, make sure the functions they exist in 
    #     change to async 
    #     """
    #     node = self.generic_visit(node)
    #     if isinstance(node.value, ast.Call):
    #         # If it's a call to an async function, make sure it's awaited
    #         if isinstance(node.value.func, ast.Name) and node.value.func.id in ['run', 'my_function']:
    #             return ast.Expr(value=ast.Await(value=node.value))
    #     return node

def collect_top_level_functions(file_path):
    with open(file_path, 'r') as f:
        source_code = f.read()
    
    tree = ast.parse(source_code)
    collector = FunctionCollector()
    collector.visit(tree)
    return list(collector.functions)

def main():
    # Set up argparse to handle command line arguments for multiple input files
    parser = argparse.ArgumentParser(description="Transform 'get' and 'set' calls into async 'await' calls.")
    parser.add_argument('input_files', nargs='+', help="The Python file(s) to transform")
    args = parser.parse_args()
    async_calls = []

    # Ensure output directory exists
    output_dir = os.path.join('output')
    os.makedirs(output_dir, exist_ok=True)

    for input_file in args.input_files:
        # Collect top-level functions
        async_calls += collect_top_level_functions(input_file)
        # print(f"Collected top-level functions from {input_file}:")
        # print(", ".join(async_calls))

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
