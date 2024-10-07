import asyncio, asyncio
import asyncio, time
from test_api.api import ExampleAPI
import asyncio, sys
posts = []

async def get_name():
    time.sleep(2)
    return 'bob'

async def make_post(post: str):
    time.sleep(2)
    posts.append(post)

async def set_profile_picture(self, picture):
    name = asyncio.ensure_future(get_name())
    post_confirmation = asyncio.ensure_future(make_post())
    old_post = asyncio.ensure_future(make_post())
    time.sleep(2)
    
    pass
    await name
    await post_confirmation
    await old_post
    if name == 'john':
        post_confirmation = asyncio.ensure_future(make_post())
        
        pass
    else:
        old_post = asyncio.ensure_future(make_post())
        
        pass
    print('picture')

async def script_function():
    name = asyncio.ensure_future(get_name(42))
    post_confirmation = asyncio.ensure_future(make_post())
    new_post = asyncio.ensure_future(make_post())
    start_time = time.time()
    
    pass
    await name
    if name == 'john':
        print('name is john')
    
    pass
    print(f'Get result: {name}')
    await post_confirmation
    print(f'Set result: {post_confirmation}')
    print(post_confirmation)
    end_time = time.time()
    print('total time ', end_time - start_time)
    
    pass
    await new_post
    my_output = new_post + 'hello'
    print(my_output)

async def script_function():
    name = asyncio.ensure_future(api.get_name(42))
    post_confirmation = asyncio.ensure_future(api.make_post())
    new_post = asyncio.ensure_future(api.make_post())
    start_time = time.time()
    api = ExampleAPI()
    
    pass
    
    pass
    await name
    if name == 'john':
        print('name is john')
    print(f'Get result: {name}')
    await post_confirmation
    print(f'Set result: {post_confirmation}')
    print(post_confirmation)
    end_time = time.time()
    print('total time ', end_time - start_time)
    
    pass
    await new_post
    my_output = new_post + 'hello'
    print(my_output)

async def my_function():
    name = asyncio.ensure_future(api.get_name(42))
    asyncio.ensure_future(script_function())
    api = ExampleAPI()
    
    pass
    print('Temporary print ')
    print('Temporary print ')
    print('Temporary print ')
    await name
    print('name is ', name)

async def non_async():
    print('this functino is not async')