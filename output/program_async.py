import asyncio, asyncio
import asyncio, time
from test_api.api import ExampleAPI
import asyncio, sys

async def script_function():
    start_time = time.time()
    api = ExampleAPI()
    name = asyncio.ensure_future(api.get_name(42))
    await name
    post_confirmation = asyncio.ensure_future(api.make_post())
    await post_confirmation
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
    script_function()
    api = ExampleAPI()
    name = asyncio.ensure_future(api.get_name(42))
    await name
    print('Temporary print ')
    print('Temporary print ')
    other_function(name)
    print('Temporary print ')
    print('name is ', name)

async def other_function(name):
    print(name)

async def non_async():
    print('this functino is not async')