import asyncio

async def basic_test():
    x = asyncio.ensure_future(get('key'))
    placeholder_code()
    placeholder_code()
    await x
    return result

async def simple_dep_async_sync():
    x = asyncio.ensure_future(get('key'))
    placeholder_code()
    await x
    result = sync_op(x)
    return result

async def simple_dep_sync_async():
    """
    Test that async invocation only get pushed up until production of dependent variable
    """
    x = sync_op('key')
    result = asyncio.ensure_future(get(x))
    placeholder_code()
    await result
    return result

async def simple_dep_async_async():
    y = asyncio.ensure_future(get('key'))
    await y
    result = asyncio.ensure_future(get(y))
    placeholder_code()
    await result
    return result

async def externalizing_order():
    y = asyncio.ensure_future(get('key'))
    placeholder_code()
    await y
    send_user_message()
    z = asyncio.ensure_future(get(y))
    placeholder_code()
    placeholder_code()
    await z

async def control_flow_simple():
    """
    Check that invocations produced inside a control flow 
    are awaited inside the control flow
    """
    temp = placeholder_code()
    if temp:
        x = asyncio.ensure_future(get('key'))
        await x
    else:
        x = asyncio.ensure_future(get('key_2'))
        await x
    return result

async def control_flow_dep_result():
    """
    Check that dependent results produced inside a control flow are awaited
    """
    temp = placeholder_code()
    if temp:
        x = asyncio.ensure_future(get('key'))
        await x
    else:
        x = asyncio.ensure_future(get('key_2'))
        await x
    return result

async def control_flow_dep_simple():
    y = asyncio.ensure_future(get('key'))
    res = placeholder_code()
    await y
    if res:
        placeholder_code(y)
    return True

async def control_flows_dep():
    y = asyncio.ensure_future(get('key'))
    x = asyncio.ensure_future(get('key'))
    z = asyncio.ensure_future(get('key'))
    await y
    if y:
        placeholder_code()
    placeholder_code()
    await x
    while x:
        placeholder_code()
    await z
    for element in z:
        placeholder_code()
    return True

async def invocation_order_with_deps():
    y = asyncio.ensure_future(get('key'))
    x = asyncio.ensure_future(get('key'))
    await x
    placeholder_code(x)
    await y
    return True

@decorator
def send_user_message(message):
    print(f'User message: {message}')