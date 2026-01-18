import ast
import argparse
import os


class SyncTransformer(ast.NodeTransformer):
    """
    Transforms Redis calls (r.X) into send_request_and_await calls.

    Signature: send_request_and_await(session_id, operation, key, new_val, old_val)
    """

    def __init__(self, redis_var='r'):
        self.redis_var = redis_var

    def visit_Call(self, node):
        # First, visit children
        self.generic_visit(node)

        # Check if this is a redis call (r.X)
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == self.redis_var:
                return self.transform_redis_call(node)

        return node

    def transform_redis_call(self, node):
        """
        Transform r.operation(args...) into send_request_and_await(session_id, operation, key, new_val, old_val)
        """
        operation = node.func.attr.upper()
        args = node.args

        # Map Redis operations to the send_request_and_await signature
        # Signature: send_request_and_await(session_id, operation, key, new_val, old_val)

        key_arg = ast.Constant(value=None)
        new_val_arg = ast.Constant(value=None)
        old_val_arg = ast.Constant(value=None)

        if operation in ('GET', 'EXISTS', 'INCR', 'DECR', 'LLEN', 'SCARD', 'SMEMBERS'):
            # Single key operations: r.get(key), r.exists(key), etc.
            if len(args) >= 1:
                key_arg = args[0]

        elif operation in ('SET', 'LPUSH', 'RPUSH', 'SADD', 'SREM'):
            # Key + value operations: r.set(key, value), r.lpush(key, value), etc.
            if len(args) >= 1:
                key_arg = args[0]
            if len(args) >= 2:
                new_val_arg = args[1]

        elif operation == 'LRANGE':
            # r.lrange(key, start, end) - pack start/end as tuple in new_val
            if len(args) >= 1:
                key_arg = args[0]
            if len(args) >= 3:
                new_val_arg = ast.Tuple(elts=[args[1], args[2]], ctx=ast.Load())

        elif operation == 'SISMEMBER':
            # r.sismember(key, member) - key and member to check
            if len(args) >= 1:
                key_arg = args[0]
            if len(args) >= 2:
                new_val_arg = args[1]

        else:
            # Generic fallback: first arg is key, rest packed into new_val
            if len(args) >= 1:
                key_arg = args[0]
            if len(args) >= 2:
                if len(args) == 2:
                    new_val_arg = args[1]
                else:
                    new_val_arg = ast.Tuple(elts=list(args[1:]), ctx=ast.Load())

        # Build the send_request_and_await call
        new_call = ast.Call(
            func=ast.Name(id='send_request_and_await', ctx=ast.Load()),
            args=[
                ast.Name(id='session_id', ctx=ast.Load()),  # session_id
                ast.Constant(value=operation),              # operation
                key_arg,                                    # key
                new_val_arg,                                # new_val
                old_val_arg,                                # old_val
            ],
            keywords=[]
        )

        return ast.copy_location(new_call, node)


def sync_transform(source_code, redis_var='r'):
    """
    Transform Redis calls to send_request_and_await calls.

    Args:
        source_code: The source code string to transform
        redis_var: The variable name used for the Redis client (default: 'r')

    Returns:
        Transformed source code string
    """
    tree = ast.parse(source_code)
    transformer = SyncTransformer(redis_var=redis_var)
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    return ast.unparse(transformed_tree)


def main():
    parser = argparse.ArgumentParser(
        description="Transform Redis calls (r.X) into send_request_and_await calls."
    )
    parser.add_argument('input_file', help="The Python file to transform")
    parser.add_argument(
        '--redis-var',
        default='r',
        help="The variable name used for Redis client (default: 'r')"
    )
    parser.add_argument(
        '-o', '--output',
        help="Output file path (default: prints to stdout)"
    )

    args = parser.parse_args()

    with open(args.input_file, 'r') as f:
        source_code = f.read()

    transformed_code = sync_transform(source_code, redis_var=args.redis_var)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(transformed_code)
        print(f"Transformed code written to {args.output}")
    else:
        print(transformed_code)


if __name__ == "__main__":
    main()
