
import asyncio
import time

storage = []

async def get():
    await asyncio.sleep(2)
    storage.append("hello")
    return 2
    
async def my_async():
    future_0 = asyncio.ensure_future(get())
    future_1 = asyncio.ensure_future(get())
    future_2 = asyncio.ensure_future(get())
    future_3 = asyncio.ensure_future(get())
    future_4 = asyncio.ensure_future(get())
    future_5 = asyncio.ensure_future(get())
    future_6 = asyncio.ensure_future(get())
    x = await future_0

    print(storage)
    
asyncio.run(my_async())