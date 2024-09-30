# main.py
import asyncio
import time
from test_api.api import ExampleAPI
import sys

def script_function():
    start_time = time.time()  # Start the timer
    # This function will be the entry point to call the ExampleAPI methods
    api = ExampleAPI()
        
    name = api.get_name(42)  # Setting a value (wait 5 seconds)
    
    post_confirmation = api.make_post()    # Getting a value (wait 3 seconds)

    print(f"Get result: {name}")

    print(f"Set result: {post_confirmation}")
    print(post_confirmation)

    end_time = time.time()  # Start the timer
    print("total time ", end_time-start_time)

    new_post = api.make_post()    # Getting a value (wait 3 seconds)
    my_output = new_post + "hello"
    print(my_output)

def my_function():
    script_function()
    
    api = ExampleAPI()

    name = api.get_name(42)  # Setting a value (wait 5 seconds)
    
    print("Temporary print ")
    print("Temporary print ")
    print("Temporary print ")

    print("name is ", name)

def non_async():
    print("this functino is not async")