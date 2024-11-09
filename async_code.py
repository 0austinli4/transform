import asyncio

@main_method
async def main_method():
    sub_method()
    placeholder_code()
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    placeholder_code()
    sub_method()
    return

async def sub_method():
    future_0 = asyncio.ensure_future(get('A'))
    await future_0
    return

def get():
    pass