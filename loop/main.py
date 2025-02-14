import subprocess
import sys
import argparse
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transforms.loop_transform import loop_push

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

# loop push down code
external_functions = []
functions_we_should_change = []
loop_push_down_code = loop_push(source_code, external_functions, functions_we_should_change)
print_to_file(loop_push_down_code, "loop_push_code.py")

print("All commands executed successfully.")
