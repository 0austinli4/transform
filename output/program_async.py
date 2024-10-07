import asyncio
import time
from test_api.api import ExampleAPI
import sys
posts = []

async def get_name():
    time.sleep(2)
    return 'bob'

async def make_post(post: str):
    time.sleep(2)
    posts.append(post)

async def set_profile_picture(self, picture):
    time.sleep(2)
    name = asyncio.ensure_future(get_name())
    await name
    if name == 'john':
        print('random stuff')
        post_confirmation = asyncio.ensure_future(make_post())
        await post_confirmation
    else:
        print('random stuff')
        old_post = asyncio.ensure_future(make_post())
        await old_post
    print('picture')

async def script_function():
    start_time = time.time()
    name = asyncio.ensure_future(get_name(42))
    await name
    if name == 'john':
        print('name is john')
    post_confirmation = asyncio.ensure_future(make_post())
    await post_confirmation
    print(f'Get result: {name}')
    print(f'Set result: {post_confirmation}')
    print(post_confirmation)
    end_time = time.time()
    print('total time ', end_time - start_time)
    new_post = asyncio.ensure_future(make_post())
    await new_post
    my_output = new_post + 'hello'
    print(my_output)

async def script_function():
    start_time = time.time()
    api = ExampleAPI()
    name = asyncio.ensure_future(api.get_name(42))
    await name
    post_confirmation = asyncio.ensure_future(api.make_post())
    await post_confirmation
    if name == 'john':
        print('name is john')
    print(f'Get result: {name}')
    print(f'Set result: {post_confirmation}')
    print(post_confirmation)
    end_time = time.time()
    print('total time ', end_time - start_time)
    new_post = asyncio.ensure_future(api.make_post())
    await new_post
    my_output = new_post + 'hello'
    print(my_output)

async def my_function():
    asyncio.ensure_future(script_function())
    api = ExampleAPI()
    name = asyncio.ensure_future(api.get_name(42))
    await name
    print('Temporary print ')
    print('Temporary print ')
    print('Temporary print ')
    print('name is ', name)

async def non_async():
    print('this functino is not async')