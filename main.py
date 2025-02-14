import subprocess
import sys
import argparse
import os
from transforms.async_transform import async_form
from transforms.async_future_push_up import async_future
from transforms.naive_await_push_down import await_push
from transforms.function_finder import find_functions_with_calls
from transforms.loop_transform import loop_push  # Added import statement for loop_push function


def print_to_file(code, output_file):
    # output_file_path = os.path.join(output_file, os.path.basename(output_file))
    with open(output_file, 'w') as f:
        f.write(code)


input_file = None

parser = argparse.ArgumentParser(description="Transform 'get' and 'set' calls into async 'await' calls.")
parser.add_argument('input_file', help="The Python file to transform")
parser.add_argument('methods', help="Comma-separated list of methods that directly use redis / backend op")
# parser.add_argument('higher_level_calls', help="Comma-separated list of methods that use lower level methods (awaits bubble up to these methods)")

args = parser.parse_args()
async_calls = [method.strip() for method in args.methods.split(',') if method.strip()]
# upper_level_calls = [method.strip() for method in args.higher_level_calls.split(',') if method.strip()]

print("Async calls", async_calls)

with open(args.input_file, 'r') as f:
    source_code = f.read()

functions_we_should_change, object_calls = find_functions_with_calls(source_code, async_calls)
async_calls.extend(object_calls)

print("Functions to touch:", functions_we_should_change)
print("Async calls", async_calls)

# async transform
async_code, external_functions = async_form(source_code, functions_we_should_change, async_calls)
print_to_file(async_code, "async_code.py")

# async future push up
async_push_up_code = async_future(async_code, external_functions)
print_to_file(async_push_up_code, "push_up.py")

# # await push down code
await_push_down_code = await_push(async_push_up_code, external_functions, functions_we_should_change)
print_to_file(await_push_down_code, "final_code.py")

# loop push down code
# loop_push_down_code = loop_push(await_push_down_code, external_functions, functions_we_should_change)
# print_to_file(loop_push_down_code, "final_code_loop_push.py")

print("All commands executed successfully.")
