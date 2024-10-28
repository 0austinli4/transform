import asyncio
import time
import numpy as np

users = ['austin', 'bob', 'mark', 'susan']

def get(user):
    time.sleep(3)  # Simulates a delay of 5 seconds
    return "Task Result"

def put(value):
    users.append(value)
    time.sleep(5)  # Simulates a delay of 5 seconds
    return True

def print_users():
    user_1 = users[0]
    value = get(user_1)
    value = value + " with append"
    put("abc")
    return

def run_function():
    t1 = time.perf_counter()
    print_users()
    t2 = time.perf_counter()
    print('Time: ', t2-t1)

run_function()