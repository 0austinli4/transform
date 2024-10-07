import subprocess
import sys

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode('utf-8'), error.decode('utf-8')
if len(sys.argv) < 2:
    print("Usage: python script.py <file1> <file2> ...")
    sys.exit(1)

input_files = sys.argv[1:]
commands = []

for file in input_files:
    commands.extend([
        f"python3 transforms/async_transform.py test_api/{file}",
        f"python3 transforms/async_future_push_up.py output/{file.replace('.py', '_async.py')}",
        f"python3 transforms/await_push_down.py output/{file.replace('.py', '_async_push.py')}"
    ])

for command in commands:
    print(f"Running command: {command}")
    output, error = run_command(command)
    
    if error:
        print(f"Error: {error}")
        sys.exit(1)
    
    print(f"Output:\n{output}")
    print("-" * 50)

print("All commands executed successfully.")
