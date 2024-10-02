# main.py
import asyncio
import time
from test_api.api import ExampleAPI
import sys

posts = []

def get_name():
    time.sleep(2)  # Simulates some data read for 3 seconds
    return "bob"

def make_post(post: str):
    time.sleep(2)
    posts.append(post)

def set_profile_picture(self, picture):
    time.sleep(2)  # Simulates waiting for 5 seconds
    name = get_name()
    print("picture")

def script_function():
    start_time = time.time()  # Start the timer
    # This function will be the entry point to call the ExampleAPI methods
    
    name = get_name(42)  # Setting a value (wait 5 seconds)

    if name == "john":
        print("name is john")
    
    post_confirmation = make_post()    # Getting a value (wait 3 seconds)

    print(f"Get result: {name}")

    print(f"Set result: {post_confirmation}")
    print(post_confirmation)

    end_time = time.time()  # Start the timer
    print("total time ", end_time-start_time)

    new_post = make_post()    # Getting a value (wait 3 seconds)
    my_output = new_post + "hello"
    print(my_output)

def script_function():
    start_time = time.time()  # Start the timer
    # This function will be the entry point to call the ExampleAPI methods
    api = ExampleAPI()
        
    name = api.get_name(42)  # Setting a value (wait 5 seconds)
    
    post_confirmation = api.make_post()    # Getting a value (wait 3 seconds)

    if name == "john":
        print("name is john")

    print(f"Get result: {name}")

    print(f"Set result: {post_confirmation}")
    print(post_confirmation)

    end_time = time.time()  
    print("total time ", end_time-start_time)

    new_post = api.make_post()    
    my_output = new_post + "hello"
    print(my_output)

def my_function():
    script_function()
    
    api = ExampleAPI()

    name = api.get_name(42)  
    
    print("Temporary print ")
    print("Temporary print ")
    print("Temporary print ")

    print("name is ", name)

def non_async():
    print("this functino is not async")
