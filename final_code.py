import asyncio

@main_method
async def main_method():
    pending_awaits = []
    future_0 = asyncio.ensure_future(get('key'))
    pending_awaits_sub_method = sub_method()
    pending_awaits.extend(pending_awaits_sub_method)
    placeholder_code()
    placeholder_code()
    pending_awaits_sub_method = sub_method()
    pending_awaits.extend(pending_awaits_sub_method)
    pending_awaits.extend([future_0])
    for await_stmt in pending_awaits:
        await await_stmt
    return pending_awaits

async def sub_method():
    pending_awaits = []
    future_0 = asyncio.ensure_future(get('A'))
    pending_awaits.extend([future_0])
    return pending_awaits

def get():
    pass