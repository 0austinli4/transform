from datetime import datetime
import time

class User:
    def __init__(self, name):
        self.name = name
        self.posts = []
        self.picture = None

    def get_name(self):
        time.sleep(2)  # Simulates some data read for 3 seconds
        return self.name

    def make_post(self, post: str):
        time.sleep(2)
        self.posts.append(post)
    
    def set_profile_picture(self, picture):
        time.sleep(2)  # Simulates waiting for 5 seconds
        name = self.get_name()
        self.picture = picture


    def script_function():
        start_time = time.time()  # Start the timer
        # This function will be the entry point to call the ExampleAPI methods
        
        name = self.get_name(42)  # Setting a value (wait 5 seconds)

        if name == "john":
            print("name is john")
        
        post_confirmation = self.make_post()    # Getting a value (wait 3 seconds)

        print(f"Get result: {name}")

        print(f"Set result: {post_confirmation}")
        print(post_confirmation)

        end_time = time.time()  # Start the timer
        print("total time ", end_time-start_time)

        new_post = self.make_post()    # Getting a value (wait 3 seconds)
        my_output = new_post + "hello"
        print(my_output)
