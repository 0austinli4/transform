def transform_redis_op(op_name, key, new_value=None, old_value=None):
    if op_name == "get":
        return [AppRequest("GET", key, None, None)]
    
    if op_name == "set":
        value = args[0]
        return [AppRequest("SET", key, value, None)]

    if op_name == "incr":
        # Increment: GET + CAS
        return [
            AppRequest("GET", key, None, None),
            AppRequest("CAS", key, "new_value", "old_value")  # Placeholder for logic
        ]

    if op_name in {"llen", "smembers", "scard", "exists", "lrange"}:
        return [AppRequest("GET", key, None, None)]

    if op_name in {"lpush", "srem", "sadd"}:
        return [
            AppRequest("GET", key, None, None),
            AppRequest("CAS", key, "new_value", "old_value")  
        ]

    if op_name == "sismember":
        return [AppRequest("GET", key, None, None)]

    raise ValueError(f"Unsupported Redis operation: {op_name}")

import ast

def transform_redis_op(node, op):
    """Transform Redis operations into AppRequest/AppResponse pairs"""
    
    # Initialize list to store AST expressions
    ast_exprs = []
    future_counter = 0
    
    def make_request_response_pair(op_name):
        nonlocal future_counter
        future_var = f"future_{future_counter}"
        future_counter += 1
        
        # Create AppRequest assignment
        request = ast.Assign(
            targets=[ast.Name(id=future_var, ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id='AppRequest', ctx=ast.Load()),
                args=[ast.Constant(value=op_name), *node.args],
                keywords=[]
            )
        )
        
        # Create AppResponse call
        response = ast.Call(
            func=ast.Name(id='AppResponse', ctx=ast.Load()),
            args=[ast.Name(id=future_var, ctx=ast.Load())],
            keywords=[]
        )
        
        return request, response, future_var
    
    op = op.upper()
    match op:
        case 'GET' | 'LLEN' | 'SCARD' | 'EXISTS' | 'SMEMBERS' | 'LRANGE' | 'SISMEMBER':
            request, response, _ = make_request_response_pair(op)
            ast_exprs.extend([request, response])
            
        case 'SET':
            request, response, _ = make_request_response_pair('SET')
            ast_exprs.extend([request, response])
            
        case 'INCR' | 'LPUSH' | 'SREM' | 'SADD':
            # First get the current value
            get_req, get_resp, get_future = make_request_response_pair('GET')
            # Then CAS with new value
            cas_req, cas_resp, _ = make_request_response_pair('CAS')
            ast_exprs.extend([get_req, get_resp, cas_req, cas_resp])
            
        case _:
            # Default to PANIC for unknown operations
            request, response, _ = make_request_response_pair('PANIC')
            ast_exprs.extend([request, response])
    
    return ast_exprs