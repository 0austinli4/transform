import subprocess
import sys
import argparse
import os
from transforms.async_transform import async_form
from transforms.async_future_push_up import async_future
from transforms.await_push_down import await_push


def print_to_file(code, output_file):
    # output_file_path = os.path.join(output_file, os.path.basename(output_file))
    with open(output_file, 'w') as f:
        f.write(code)


input_file = None

parser = argparse.ArgumentParser(description="Transform 'get' and 'set' calls into async 'await' calls.")
parser.add_argument('input_file', help="The Python file to transform")
parser.add_argument('methods', help="Comma-separated list of methods to transform")
args = parser.parse_args()
async_calls = [method.strip() for method in args.methods.split(',')]

with open(args.input_file, 'r') as f:
    source_code = f.read()

# async transform
async_code, external_functions = async_form(source_code, async_calls)
print_to_file(async_code, "async_code.py")

# async future push up
async_push_up_code = async_future(async_code, external_functions)
print_to_file(async_push_up_code, "push_up.py")

# # await push down code
await_push_down_code = await_push(async_push_up_code, external_functions)
print_to_file(await_push_down_code, "final_code.py")

print("All commands executed successfully.")
