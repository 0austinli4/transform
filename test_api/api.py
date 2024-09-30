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
