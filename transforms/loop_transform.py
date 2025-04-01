import ast
import argparse
import os
from collections import deque


class VariableCollector(ast.NodeVisitor):
    def __init__(self):
        self.variables = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            self.visit(node.func.value)

        for arg in node.args:
            self.visit(arg)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.variables.append(node.id)

    def visit_If(self, node):
        self.visit(node.test)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            self.variables.append(node.value.id)
        self.visit(node.value)

    def generic_visit(self, node):
        for child in ast.iter_child_nodes(node):
            self.visit(child)


def get_variables_used(stmt):
    collector = VariableCollector()
    collector.visit(stmt)
    return collector.variables


class AwaitMover(ast.NodeTransformer):
    def __init__(self, external_functions, async_funcs):
        self.external_functions = set(external_functions)
        self.async_funcs = async_funcs
        self.nesting = 0
        self.var_dependencies = {}
        self.app_response_vars = set()
        self.var_usages = {}
        self.is_for_loop_with_apprequest = False

    def track_dependencies(self, node):
        """
        Track dependencies between variables
        Specifically look for:
        1. AppResponse variable assignments
        2. Variables that use AppResponse results
        """
        print(f"\n--- Tracking Dependencies for Node: {type(node)} ---")

        # Track AppResponse variable assignments
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "AppResponse"
        ):
            # Get the target variable name
            if node.targets and isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                self.app_response_vars.add(var_name)
                print(f"[DEBUG] Tracked AppResponse variable: {var_name}")

        # Track variable usages, especially of AppResponse variables
        if isinstance(node, ast.Assign):
            # Check if the right side uses any AppResponse variables
            # used_vars = self.extract_used_vars(node.value)
            used_vars = []
            print(f"[DEBUG] Used variables in assignment: {used_vars}")
            for used_var in used_vars:
                if used_var in self.app_response_vars:
                    print(f"[DEBUG] Variable dependency: {used_var} used in assignment")

                    # Track the target variable
                    if node.targets and isinstance(node.targets[0], ast.Name):
                        target_var = node.targets[0].id
                        self.var_dependencies[target_var] = used_var
                        print(
                            f"[DEBUG] Dependency tracked: {target_var} depends on {used_var}"
                        )

        # Track method calls and subscript accesses
        if isinstance(node, ast.Call) or isinstance(node, ast.Subscript):
            used_vars = self.extract_used_vars(node)
            print(f"[DEBUG] Used variables in call/subscript: {used_vars}")
            for used_var in used_vars:
                if used_var in self.app_response_vars:
                    print(
                        f"[DEBUG] AppResponse variable used in method/subscript: {used_var}"
                    )

    # def extract_used_vars(self, node):
    #     """
    #     Extract variable names used in a node
    #     """
    #     used_vars = set()

    #     # Recursive extraction of variable names
    #     def extract(n):
    #         print(f"[EXTRACT] Examining node type: {type(n)}")
    #         if isinstance(n, ast.Name):
    #             used_vars.add(n.id)
    #             print(f"[EXTRACT] Found variable name: {n.id}")
    #         elif isinstance(n, ast.Attribute):
    #             print(f"[EXTRACT] Found attribute: {n.attr}")
    #             extract(n.value)
    #         elif isinstance(n, ast.Subscript):
    #             print(f"[EXTRACT] Found subscript")
    #             extract(n.value)
    #             extract(n.slice)
    #         elif isinstance(n, ast.Call):
    #             print(f"[EXTRACT] Found call")
    #             extract(n.func)
    #             for arg in n.args:
    #                 extract(arg)
    #             for kw in n.keywords:
    #                 extract(kw.value)

    #     extract(node)
    #     return used_vars

    def visit_FunctionDef(self, node):
        is_loop_optimization = any(
            isinstance(dec, ast.Name) and dec.id == "enable_loop_optimization"
            for dec in node.decorator_list
        )
        if not is_loop_optimization:
            return node

        self.var_dependencies.clear()
        self.all_awaits = set()
        node.body = self.process_body(node.body)
        if self.is_for_loop_with_apprequest:
            dep_vars_init = ast.Assign(
                targets=[ast.Name(id="dep_vars_queue", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id="deque", ctx=ast.Load()), args=[], keywords=[]
                ),
            )
            node.body.insert(0, dep_vars_init)

            self.is_for_loop_with_apprequest = False
        return node

    def process_body(self, body):
        self.nesting += 1
        final_body = []

        for stmt in body:
            # Check if the statement is an AppResponse call
            if self.is_app_response_call(stmt):
                continue

            result = self.visit(stmt)

            if isinstance(result, list):
                final_body.extend(result)
            else:
                final_body.append(result)

        return final_body

    def visit_For(self, node):
        # if it's the await loop, ignore
        if self.check_exact_await_loop(node):
            return node

        app_response_produced = set()  # Variables related to AppResponse
        dependent_vars = set()  # Variables dependent on AppResponse
        variable_queue = deque()

        # First pass: identify variables and dependencies
        first_for_loop = []
        second_for_loop = []
        vars_produced_first_pass = set()
        vars_used_from_app_response = []
        dep_statements_second_loop = []

        # Pass 1: find all app response calls and the variables they produce
        # do this by finding app response and get_vars_produced
        # Pass 2: find all dependent variables to vars_produced_app_response
        # move them to the second loop
        # Pass 3: find if the dependent vars depend on anything above first AppResponse
        # duplicate these
        # queue object
        # depdenedices by variables used vs. produed originally

        # PASS 1 - FIND APPRESPONSE CALLS
        for stmt in node.body:
            # Identify AppResponse calls
            if self.is_pending_await_remove(stmt):
                continue
            if self.is_app_response_call(stmt):
                # first_for_loop.pop()
                # Modify the AppResponse call to use dep_var_queue.pop()
                app_response_produced.update([target.id for target in stmt.targets])
                stmt.value.args = [
                    ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="dep_vars_queue", ctx=ast.Load()),
                            attr="popleft",
                            ctx=ast.Load(),
                        ),
                        args=[],
                        keywords=[],
                    )
                ]
                # add to second for loop
                second_for_loop.append(stmt)
                self.is_for_loop_with_apprequest = True
                continue

            vars_produced_first_pass.update(get_variables_produced(stmt))

            for var in vars_used_from_app_response:
                if var not in vars_produced_first_pass or "future" in var:
                    continue
                dep_vars_queue_add = ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="dep_vars_queue", ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[ast.Name(id=var, ctx=ast.Load())],
                        keywords=[],
                    )
                )
                first_for_loop.append(dep_vars_queue_add)
                variable_queue.append(var)

            if len(app_response_produced) > 0:
                vars_used = get_variables_used(stmt)

                if set(vars_used).intersection(app_response_produced):
                    # Add each intersecting variable to dep_vars_queue
                    # if these have key words, then we need to move them
                    second_for_loop.append(stmt)
                    dep_statements_second_loop.append(stmt)
                else:
                    first_for_loop.append(stmt)
                    # second_for_loop.append(stmt)
                vars_used_from_app_response.extend(vars_used)
            else:
                first_for_loop.append(stmt)

        if not self.is_for_loop_with_apprequest:
            return node

        for stmt in node.body:
            if self.is_pending_await_add(stmt):
                # Transform to dep_vars_queue.append()
                stmt.value.func = ast.Attribute(
                    value=ast.Name(id="dep_vars_queue", ctx=ast.Load()),
                    attr="append",
                    ctx=ast.Load(),
                )

        for stmt in dep_statements_second_loop:
            # Check if any variables used in the statement are in variable_queue
            vars_used = get_variables_used(stmt)
            intersecting_vars = set(vars_used).intersection(variable_queue)

            if intersecting_vars:
                # Create a transformer to replace variables
                class VariableReplacer(ast.NodeTransformer):
                    def visit_Name(self, node):
                        if node.id in intersecting_vars:
                            # Replace with dep_vars_queue.popleft()
                            return ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id="dep_vars_queue", ctx=ast.Load()),
                                    attr="popleft",
                                    ctx=ast.Load(),
                                ),
                                args=[],
                                keywords=[],
                            )
                        return node

                # Transform the statement
                transformer = VariableReplacer()
                modified_stmt = transformer.visit(stmt)

                # Replace the original statement with the modified one
                second_for_loop[second_for_loop.index(stmt)] = modified_stmt

        # Update the for loop bodies
        node.body = first_for_loop

        # If we found AppResponse calls or dependent lines, create a new for loop
        if second_for_loop:
            app_response_loop = ast.For(
                target=node.target,
                iter=node.iter,
                body=second_for_loop,
                orelse=node.orelse,
            )
            return [node, app_response_loop]
        return node

    def is_pending_await_add(self, stmt):
        return (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute)
            and isinstance(stmt.value.func.value, ast.Name)
            and stmt.value.func.value.id == "pending_awaits"
            and stmt.value.func.attr == "add"
        )

    def is_pending_await_remove(self, stmt):
        return (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute)
            and isinstance(stmt.value.func.value, ast.Name)
            and stmt.value.func.value.id == "pending_awaits"
            and stmt.value.func.attr == "remove"
        )

    def visit_Assign(self, node):
        # Check for AppResponse calls in assignments
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "AppResponse"
        ):
            # skip assignment
            return None
        return node

    def visit_Expr(self, node):
        # Check for direct AppResponse calls
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "AppResponse"
        ):
            # Skip this expression in the first pass
            return None
        return node

    def is_ensure_future_call(self, node):
        if isinstance(node, ast.Assign):
            node = node.value
            return (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "asyncio"
                and node.func.attr == "ensure_future"
            )
        return False

    def get_return_stmt(self, stmt):
        if stmt.value:
            stmt.value = ast.Tuple(
                elts=[ast.Name(id="pending_awaits", ctx=ast.Load()), stmt.value],
                ctx=ast.Load(),
            )
        else:
            # If empty return, return tuple (pending_awaits, None)
            stmt.value = ast.Tuple(
                elts=[
                    ast.Name(id="pending_awaits", ctx=ast.Load()),
                    ast.Constant(value=None),
                ],
                ctx=ast.Load(),
            )
        return stmt

    def get_await_variable_name(self, stmt):
        # Check for assignment statements where the value is an await expression
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Await):
            target = stmt.targets[0]
            if isinstance(target, ast.Name):
                return [target.id]
            elif isinstance(target, ast.Tuple):  # Handle tuple assignments
                return [name.id for name in target.elts if isinstance(name, ast.Name)]
            elif isinstance(
                target, ast.Attribute
            ):  # Handle attributes, e.g., obj.attr = await ...
                return [target.attr]
        # Check for expression statements where the expression is an await
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Await):
            if isinstance(stmt.value.value, ast.Name):
                return [stmt.value.value.id]
        return None

    def get_future_names(self, stmt):
        # Handle assignment statements
        if isinstance(stmt, ast.Assign):
            target = stmt.targets[0]
            if isinstance(target, ast.Name):
                return [target.id]
            elif isinstance(target, ast.Tuple):
                return [name.id for name in target.elts if isinstance(name, ast.Name)]
            elif isinstance(target, ast.Attribute):
                return [target.attr]
        return []

    def is_async_function_call(self, stmt):
        # Needs to handle both function calls and attribute calls
        # Handle expression statements
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            if isinstance(stmt.value.func, ast.Name):
                return stmt.value.func.id in self.async_funcs
            elif isinstance(stmt.value.func, ast.Attribute):
                return stmt.value.func.attr in self.async_funcs
        # Handle assignments
        elif isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
            if isinstance(stmt.value.func, ast.Name):
                return stmt.value.func.id in self.async_funcs
            elif isinstance(stmt.value.func, ast.Attribute):
                return stmt.value.func.attr in self.async_funcs
        return False

    def is_await_call(self, node):
        return (isinstance(node, ast.Expr) and isinstance(node.value, ast.Await)) or (
            isinstance(node, ast.Assign) and isinstance(node.value, ast.Await)
        )

    def is_app_response_call(self, stmt):
        if (
            isinstance(stmt, ast.Assign)
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Name)
            and stmt.value.func.id == "AppResponse"
        ):
            return True

        # Check for direct call pattern: AppResponse(x)
        if (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Name)
            and stmt.value.func.id == "AppResponse"
        ):
            return True

        return False

    def is_app_request_call(self, node):
        # Check for expression statements
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                return node.value.func.id == "AppRequest"
        # Check for assignments where the value is an AppRequest call
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                return node.value.func.id == "AppRequest"
        return False

    def is_external_function_call(self, node):
        return (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id in self.external_functions
        )

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

    def get_docstring(self, node):
        docstring = ast.get_docstring(node)
        return docstring

    def handle_main_method(self, node):
        node = ast.AsyncFunctionDef(
            name=node.name,
            args=node.args,
            body=node.body,
            decorator_list=node.decorator_list,
            returns=node.returns,
            type_comment=node.type_comment if hasattr(node, "type_comment") else None,
        )
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.Return):
                # Insert the await loop before the return
                node.body.insert(i, self.create_await_loop())
                break
        else:
            node.body.append(self.create_await_loop())
        return node

    def handle_assign(self, stmt, pending_var):
        if isinstance(stmt, ast.Assign):
            # Case where the function call is being assigned
            target = stmt.targets[0]

            if isinstance(target, ast.Tuple):
                # For tuple unpacking, preserve the original elements
                tuple_elts = [ast.Name(id=pending_var, ctx=ast.Store())]
                tuple_elts.extend(target.elts)

                # Create new tuple with pending_awaits as first element
                tuple_assign = ast.Assign(
                    targets=[ast.Tuple(elts=tuple_elts, ctx=ast.Store())],
                    value=stmt.value,
                )
                return tuple_assign
            else:
                # Single variable assignment
                tuple_assign = ast.Assign(
                    targets=[
                        ast.Tuple(
                            elts=[ast.Name(id=pending_var, ctx=ast.Store()), target],
                            ctx=ast.Store(),
                        )
                    ],
                    value=stmt.value,
                )
                return tuple_assign
        else:
            # Case where function call is just an expression
            assign_stmt = ast.Assign(
                targets=[
                    ast.Tuple(
                        elts=[
                            ast.Name(id=pending_var, ctx=ast.Store()),
                            ast.Name(id="_", ctx=ast.Store()),
                        ],
                        ctx=ast.Store(),
                    )
                ],
                value=stmt.value,
            )
            return assign_stmt

    def update_statement(self, pending_var):
        return ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id="pending_awaits", ctx=ast.Load()),
                    attr="update",
                    ctx=ast.Load(),
                ),
                args=[ast.Name(id=pending_var, ctx=ast.Load())],
                keywords=[],
            )
        )

    def check_exact_await_loop(self, node):
        if (
            isinstance(node.target, ast.Name)
            and node.target.id == "future"
            and isinstance(node.iter, ast.Name)
            and node.iter.id == "pending_awaits"
            and len(node.body) == 1
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Call)
            and isinstance(node.body[0].value.func, ast.Name)
            and node.body[0].value.func.id == "AppResponse"
            and len(node.body[0].value.args) == 1
            and isinstance(node.body[0].value.args[0], ast.Name)
            and node.body[0].value.args[0].id == "future"
            and not node.orelse
        ):
            return True  # Do nothing and return the original node


def get_variables_produced(stmt):
    """
    Extract variable names that are produced (assigned) by a statement

    Args:
        stmt (ast.AST): The AST node to analyze

    Returns:
        set: Set of variable names produced by the statement
    """
    produced_vars = set()

    # Handle assignment statements
    if isinstance(stmt, ast.Assign):
        for target in stmt.targets:
            # Handle simple name assignments
            if isinstance(target, ast.Name):
                produced_vars.add(target.id)

            # Handle tuple/list unpacking
            elif isinstance(target, (ast.Tuple, ast.List)):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        produced_vars.add(elt.id)

    # Handle augmented assignments (+=, -=, etc.)
    elif isinstance(stmt, ast.AugAssign):
        if isinstance(stmt.target, ast.Name):
            produced_vars.add(stmt.target.id)

    # Handle for loop targets
    elif isinstance(stmt, ast.For):
        if isinstance(stmt.target, ast.Name):
            produced_vars.add(stmt.target.id)
        elif isinstance(stmt.target, (ast.Tuple, ast.List)):
            for elt in stmt.target.elts:
                if isinstance(elt, ast.Name):
                    produced_vars.add(elt.id)

    return produced_vars


def main():
    parser = argparse.ArgumentParser(
        description="Transform async code to append all awaits at the bottom."
    )
    parser.add_argument(
        "input_files", nargs="+", help="The Python file(s) to transform"
    )
    args = parser.parse_args()

    output_dir = os.path.join("..", "output")
    os.makedirs(output_dir, exist_ok=True)

    for input_file in args.input_files:
        with open(input_file, "r") as f:
            source_code = f.read()

        tree = ast.parse(source_code)
        transformer = AwaitMover([], [])
        transformed_tree = transformer.visit(tree)
        ast.fix_missing_locations(transformed_tree)

        new_source_code = ast.unparse(transformed_tree)

        output_file = input_file.replace(".py", "_down.py")
        output_file_path = os.path.join(output_dir, os.path.basename(output_file))

        with open(output_file_path, "w") as f:
            f.write(new_source_code)

        print(f"Transformed code has been written to {output_file_path}.")


if __name__ == "__main__":
    main()


def loop_push(source_code, external_functions, asnyc_functions):
    tree = ast.parse(source_code)
    transformer = AwaitMover(external_functions, asnyc_functions)
    transformer.current_node = tree
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    return ast.unparse(transformed_tree)
