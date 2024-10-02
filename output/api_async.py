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
        await name
        self.picture = picture

    async def script_function():
        start_time = time.time()
        name = asyncio.ensure_future(self.get_name(42))
        await name
        if name == 'john':
            print('name is john')
        post_confirmation = asyncio.ensure_future(self.make_post())
        await post_confirmation
        print(f'Get result: {name}')
        print(f'Set result: {post_confirmation}')
        print(post_confirmation)
        end_time = time.time()
        print('total time ', end_time - start_time)
        new_post = asyncio.ensure_future(self.make_post())
        await new_post
        my_output = new_post + 'hello'
        print(my_output)