import asyncio
'\nTest file for IOC ordering \n\nAsync operations: GET \n\nSync operations: SYNC_OP\n\nplaceholder_code() represents any sequence of code that is not involved in the transformation \ni.e., not dependent, not sychronous or async calls. Invocations and responses can freely move\nbetween these portions of code\n\nsend_user_message() represents an externalized function (with decoration). Invocations and\nresponses should be restricted by the location of these statements. \n'

async def basic_test():
    """
    Test that awaits are pushed to bottom, and invocations are pushed to top
    """
    placeholder_code()
    x = asyncio.ensure_future(get('key'))
    await x
    placeholder_code()
    return result

async def simple_dep_async_sync():
    """
    Test that awaits only get pushed down until dependency
    """
    x = asyncio.ensure_future(get('key'))
    await x
    placeholder_code()
    result = sync_op(x)
    return result

async def simple_dep_sync_async():
    """
    Test that async invocation only get pushed up until production of dependent variable
    """
    x = sync_op('key')
    placeholder_code()
    result = asyncio.ensure_future(get(x))
    await result
    return result

async def simple_dep_async_async():
    """
    Test that async invocation only get pushed up until production of dependent variable
    """
    y = asyncio.ensure_future(get('key'))
    await y
    placeholder_code()
    result = asyncio.ensure_future(get(y))
    await result
    return result

async def externalizing_order():
    """
    Test that async invocation only get pushed up until production of dependent variable
    """
    y = asyncio.ensure_future(get('key'))
    await y
    placeholder_code()
    send_user_message()
    placeholder_code()
    placeholder_code()
    z = asyncio.ensure_future(get(y))
    await z

async def control_flow_simple():
    """
    Check that invocations produced inside a control flow are awaited inside the control flow
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
    """
    Check that a response used inside a control flow is awaited outside of that contorl flow
    """
    y = asyncio.ensure_future(get('key'))
    await y
    res = placeholder_code()
    if res:
        placeholder_code(y)
    return True

async def control_flows_dep():
    y = asyncio.ensure_future(get('key'))
    await y
    if y:
        placeholder_code()
    x = asyncio.ensure_future(get('key'))
    await x
    placeholder_code()
    while x:
        placeholder_code()
    z = asyncio.ensure_future(get('key'))
    await z
    for element in z:
        placeholder_code()
    return True

async def invocation_order_with_deps():
    """
    Check that when two operations are awaited and second is used as dependency, 
    first one is awaited first
    """
    y = asyncio.ensure_future(get('key'))
    await y
    x = asyncio.ensure_future(get('key'))
    await x
    placeholder_code(x)
    return True

@decorator
def send_user_message(message):
    print(f'User message: {message}')