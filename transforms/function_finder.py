import ast

class CallFinder(ast.NodeVisitor):
    def __init__(self, target_functions):
        self.target_functions = set(target_functions)
        self.functions_with_calls = set()
        self.current_function = None
        self.call_graph = {}  # Track function calls
        self.object_calls = set()  # Track methods called on target objects

    def visit_FunctionDef(self, node):
        previous_function = self.current_function
        self.current_function = node.name
        self.call_graph[self.current_function] = set()  # Initialize empty set for this function
        self.generic_visit(node)
        self.current_function = previous_function

    def visit_Call(self, node):
        if self.current_function:  # Only check if we're inside a function
            obj_name, func_name = self.get_func_name(node)
            if func_name:
                # Add to call graph
                call_signature = f"{obj_name}.{func_name}" if obj_name else func_name
                self.call_graph[self.current_function].add(call_signature)
                # Check both the object name and function name against target functions
                if (func_name in self.target_functions or 
                    (obj_name and obj_name in self.target_functions)):
                    self.functions_with_calls.add(self.current_function)
                    # If this is a method call on a target object, add the full qualified name
                    if obj_name and obj_name in self.target_functions:
                        self.object_calls.add(f"{obj_name}.{func_name}")
        self.generic_visit(node)

    def get_func_name(self, node):
        if isinstance(node.func, ast.Name):
            return None, node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id, node.func.attr
            return None, node.func.attr
        return None, None

    def find_all_callers(self):
        """Find all functions in the call chain that eventually lead to target functions"""
        result = set()
        work_list = list(self.functions_with_calls)
        
        # Keep processing until no new functions are found
        while work_list:
            current = work_list.pop()
            result.add(current)
            
            # Find all functions that call the current function
            for func, calls in self.call_graph.items():
                if current in calls and func not in result:
                    work_list.append(func)
        
        return result

def find_functions_with_calls(source_code, target_functions):
    if isinstance(source_code, str):
        tree = ast.parse(source_code)
    else:
        tree = source_code  # Assume it's already an AST
    finder = CallFinder(target_functions)
    finder.visit(tree)
    return finder.find_all_callers(), finder.object_calls
