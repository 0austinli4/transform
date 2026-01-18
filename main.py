import subprocess
import sys
import argparse
import os
from transforms.async_transform import async_form
from transforms.async_future_push_up import async_future
from transforms.naive_await_push_down import await_push
from transforms.function_finder import find_functions_with_calls
from transforms.loop_transform import loop_push  # Added import statement for loop_push function
from transforms.sync_transform import sync_transform


def print_to_file(code, output_file):
    # output_file_path = os.path.join(output_file, os.path.basename(output_file))
    with open(output_file, 'w') as f:
        f.write(code)


def run_async_transform(source_code, async_calls):
    """Run the full async transformation pipeline."""
    functions_we_should_change, object_calls = find_functions_with_calls(source_code, async_calls)
    async_calls.extend(object_calls)

    print("Functions to touch:", functions_we_should_change)
    print("Async calls", async_calls)

    # async transform
    async_code, external_functions = async_form(source_code, functions_we_should_change, async_calls)
    print_to_file(async_code, "intermediate_transform/async_code.py")

    # async future push up
    async_push_up_code = async_future(async_code, external_functions)
    print_to_file(async_push_up_code, "intermediate_transform/push_up.py")

    # await push down code
    await_push_down_code = await_push(async_push_up_code, external_functions, functions_we_should_change)
    print_to_file(await_push_down_code, "final_code.py")

    # loop push down code
    loop_push_down_code = loop_push(await_push_down_code, external_functions, functions_we_should_change)
    print_to_file(loop_push_down_code, "final_code_loop_optimization.py")

    print("Async transform completed successfully.")


def run_sync_transform(source_code, redis_var='r', output_file='sync_transformed.py'):
    """Run the synchronous transformation (Redis calls → send_request_and_await)."""
    transformed_code = sync_transform(source_code, redis_var=redis_var)
    print_to_file(transformed_code, output_file)
    print(f"Sync transform completed. Output written to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Transform Python code: async pipeline or sync Redis replacement."
    )
    parser.add_argument('input_file', help="The Python file to transform")
    parser.add_argument(
        'methods',
        nargs='?',
        default='',
        help="Comma-separated list of methods that directly use redis / backend op (required for async mode)"
    )
    parser.add_argument(
        '--sync',
        action='store_true',
        help="Run sync transform (replace Redis calls with send_request_and_await)"
    )
    parser.add_argument(
        '--redis-var',
        default='r',
        help="Variable name for Redis client (default: 'r', used with --sync)"
    )
    parser.add_argument(
        '-o', '--output',
        default='sync_transformed.py',
        help="Output file for sync transform (default: sync_transformed.py)"
    )

    args = parser.parse_args()

    with open(args.input_file, 'r') as f:
        source_code = f.read()

    if args.sync:
        # Sync transform mode
        run_sync_transform(source_code, redis_var=args.redis_var, output_file=args.output)
    else:
        # Async transform mode (original behavior)
        if not args.methods:
            parser.error("methods argument is required for async transform mode")
        async_calls = [method.strip() for method in args.methods.split(',') if method.strip()]
        print("Async calls", async_calls)
        run_async_transform(source_code, async_calls)

    print("All commands executed successfully.")


if __name__ == '__main__':
    main()
