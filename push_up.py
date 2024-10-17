import asyncio
'\nTest file for IOC ordering \n\nAsync operations: GET \n\nSync operations: SYNC_OP\n\nplaceholder_code() represents any sequence of code that is not involved in the transformation \ni.e., not dependent, not sychronous or async calls. Invocations and responses can freely move\nbetween these portions of code\n\nsend_user_message() represents an externalized function (with decoration). Invocations and\nresponses should be restricted by the location of these statements. \n'

async def basic_test():
    x = asyncio.ensure_future(get('key'))
    await x
    '\n    Test that awaits are pushed to bottom, and invocations are pushed to top\n    '
    placeholder_code()
    placeholder_code()
    return result

async def simple_dep_async_sync():
    x = asyncio.ensure_future(get('key'))
    await x
    '\n    Test that awaits only get pushed down until dependency\n    '
    placeholder_code()
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
    await result
    '\n    Test that async invocation only get pushed up until production of dependent variable\n    '
    placeholder_code()
    return result

async def externalizing_order():
    y = asyncio.ensure_future(get('key'))
    await y
    '\n    Test that async invocation only get pushed up until production of dependent variable\n    '
    placeholder_code()
    send_user_message()
    z = asyncio.ensure_future(get(y))
    await z
    placeholder_code()
    placeholder_code()

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
    y = asyncio.ensure_future(get('key'))
    await y
    '\n    Check that a response used inside a control flow is awaited outside of that contorl flow\n    '
    res = placeholder_code()
    if res:
        placeholder_code(y)
    return True

async def control_flows_dep():
    y = asyncio.ensure_future(get('key'))
    await y
    x = asyncio.ensure_future(get('key'))
    await x
    z = asyncio.ensure_future(get('key'))
    await z
    if y:
        placeholder_code()
    placeholder_code()
    while x:
        placeholder_code()
    for element in z:
        placeholder_code()
    return True

async def invocation_order_with_deps():
    y = asyncio.ensure_future(get('key'))
    await y
    x = asyncio.ensure_future(get('key'))
    await x
    '\n    Check that when two operations are awaited and second is used as dependency, \n    first one is awaited first\n    '
    placeholder_code(x)
    return True

@decorator
def send_user_message(message):
    print(f'User message: {message}')