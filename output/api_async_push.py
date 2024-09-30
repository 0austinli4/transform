from datetime import datetime
import asyncio, time

class User:

    async def __init__(self, name):
        self.name = name
        self.posts = []
        self.picture = None

    async def get_name(self):
        time.sleep(2)
        return self.name

    async def make_post(self, post: str):
        time.sleep(2)
        self.posts.append(post)

    async def set_profile_picture(self, picture):
        time.sleep(2)
        name = asyncio.ensure_future(self.get_name())
        
        pass
        self.picture = picture
        await name