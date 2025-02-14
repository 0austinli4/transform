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
            # Original method call tracking logic
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
        """
        Enhanced function to extract function/method names with better handling of complex calls
        
        Returns:
            tuple: (object_name, function_name)
        """
        # Handle direct function calls
        if isinstance(node.func, ast.Name):
            return None, node.func.id
        
        # Handle method calls
        elif isinstance(node.func, ast.Attribute):
            # Full method call as a string
            full_method_call = []
            current = node.func
            
            # Traverse down the attribute chain
            while isinstance(current, ast.Attribute):
                full_method_call.insert(0, current.attr)
                current = current.value
            
            # Check if it's a method on a name
            if isinstance(current, ast.Name):
                full_method_call.insert(0, current.id)
            
            # Join the full method call
            full_call_str = '.'.join(full_method_call)
            
            # Split the last part as the method name
            parts = full_call_str.split('.')
            if len(parts) > 1:
                return '.'.join(parts[:-1]), parts[-1]
            
            return None, full_call_str
        
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
