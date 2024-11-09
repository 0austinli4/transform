import ast

class CallFinder(ast.NodeVisitor):
    def __init__(self, target_functions):
        self.target_functions = set(target_functions)
        self.functions_with_calls = set()
        self.current_function = None

    def visit_FunctionDef(self, node):
        previous_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = previous_function

    def visit_Call(self, node):
        if self.current_function:  # Only check if we're inside a function
            func_name = self.get_func_name(node)
            if func_name in self.target_functions:
                self.functions_with_calls.add(self.current_function)
        self.generic_visit(node)

    def get_func_name(self, node):
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

def find_functions_with_calls(source_code, target_functions):
    """
    Returns a list of function names that contain calls to any of the target functions.
    
    Args:
        source_code (str): The Python source code to analyze
        target_functions (list): List of function names to look for
        
    Returns:
        list: Names of functions that call any of the target functions
    """
    tree = ast.parse(source_code)
    finder = CallFinder(target_functions)
    finder.visit(tree)
    return list(finder.functions_with_calls)