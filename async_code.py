import asyncio
'\nTest file for IOC ordering \n\nAsync operations: GET \n\nSync operations: SYNC_OP\n\nplaceholder_code() represents any sequence of code that is not involved in the transformation \ni.e., not dependent, not sychronous or async calls. Invocations and responses can freely move\nbetween these portions of code\n\nsend_user_message() represents an externalized function (with decoration). Invocations and\nresponses should be restricted by the location of these statements. \n'

async def basic_test():
    """
    Test that awaits are pushed to bottom, and invocations are pushed to top
    """
    placeholder_code()
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    placeholder_code()
    return result

async def simple_dep_async_sync():
    """
    Test that awaits only get pushed down until dependency
    """
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    placeholder_code()
    result = sync_op(x)
    return result

async def simple_dep_sync_async():
    """
    Test that async invocation only get pushed up until production of dependent variable
    """
    x = sync_op('key')
    placeholder_code()
    future_0 = asyncio.ensure_future(get(x))
    result = await future_0
    return result

async def simple_dep_async_async():
    """
    Test that async invocation only get pushed up until 
    production of dependent variable with another async
    """
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    placeholder_code()
    future_1 = asyncio.ensure_future(get(y))
    result = await future_1
    return result

async def externalizing_order():
    """
    Test ordering with external functions
    """
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    placeholder_code()
    send_user_message()
    placeholder_code()
    placeholder_code()
    future_1 = asyncio.ensure_future(get(y))
    z = await future_1

async def control_flow_simple():
    """
    Check that invocations produced inside a control flow are awaited inside the control flow
    """
    temp = placeholder_code()
    if temp:
        future_0 = asyncio.ensure_future(get('key'))
        x = await future_0
    else:
        future_1 = asyncio.ensure_future(get('key_2'))
        x = await future_1
    return result

async def control_flow_dep_result():
    """
    Check that dependent results produced inside a control flow are awaited
    """
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    if temp:
        future_1 = asyncio.ensure_future(get(x))
        result = await future_1
    else:
        future_2 = asyncio.ensure_future(get('key_2'))
        result = await future_2
    return result

async def control_flow_dep_simple():
    """
    Check that a response used inside a control flow is awaited outside of that contorl flow
    """
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    res = placeholder_code()
    if res:
        placeholder_code(y)
    return True

async def control_flows_dep():
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    if y:
        placeholder_code()
    future_1 = asyncio.ensure_future(get('key'))
    x = await future_1
    placeholder_code()
    while x:
        placeholder_code()
    future_2 = asyncio.ensure_future(get('key'))
    z = await future_2
    for element in z:
        placeholder_code()
    return True

async def control_flows_dep_inside():
    placeholder_code()
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    while True:
        placeholder_code(x)
    future_1 = asyncio.ensure_future(get('key'))
    z = await future_1
    for element in list:
        placeholder_code(z)
    return True

async def invocation_order_with_deps():
    """
    Check that when two operations are awaited and second is used as dependency, 
    we pop out only the dependency and push the response (does not have to be
    in order)
    """
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    future_1 = asyncio.ensure_future(get('key'))
    x = await future_1
    placeholder_code(x)
    return True

async def function_def_without_result():
    future_0 = asyncio.ensure_future(get('key'))
    await future_0
    placeholder_code()
    placeholder_code()
    placeholder_code()
    return True

async def function_as_if():
    future_0 = asyncio.ensure_future(get('key'))
    async_cond_0 = await future_0
    if async_cond_0:
        placeholder_code()
    return True

def function_for():
    future_0 = asyncio.ensure_future(get('key'))
    async_iter_0 = await future_0
    for element in async_iter_0:
        placeholder_code()
    return True

async def function_as_if():
    """
    Check that when two operations are awaited and second is used as dependency, 
    we pop out only the dependency and push the response (does not have to be
    in order)
    """
    future_0 = asyncio.ensure_future(get('key'))
    async_cond_0 = await future_0
    while async_cond_0:
        placeholder_code()
    return True

@decorator
def send_user_message(message):
    print(f'User message: {message}')