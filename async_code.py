import asyncio
'\nTest file for program transformations\n\nAsync operations: \n    - GET \n\nSync operations:\n    - SYNC_OP\n    - placeholder_code()\n\nplaceholder_code() represents any sequence of code that is not involved in the transformation \ni.e., not dependent code or an async calls. Invocations and responses can freely move\nbetween these portions of code\n\nsend_user_message() represents an externalized function (defined via decoration). Invocations and\nresponses should be restricted by the location of these statements. \n\n'

async def basic_test():
    """
    Test that awaits are pushed to bottom, and invocations are pushed to top
    """
    placeholder_code()
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    placeholder_code()
    return result

async def basic_test_dep_await():
    """
    Test that awaits only get pushed down until dependency
    """
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    placeholder_code()
    result = sync_op(x)
    return result

async def basic_test_dep_invoke():
    """
    Test that async invocation only get pushed up until production of dependent variable
    """
    x = sync_op('key')
    placeholder_code()
    future_0 = asyncio.ensure_future(get(x))
    result = await future_0
    return result

async def basic_test_dep_asyncs():
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

async def basic_test_externalizing_order():
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

async def basic_test_control_flow():
    """
    Check that awaits and invocations can move past control flow statements
    """
    if placeholder_code():
        placeholder_code()
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    if res:
        placeholder_code(y)
    return True

async def control_flow_dep_comparator():
    """
    Check that dependent results used inside a comparison
    """
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    if x:
        placeholder_code()
    else:
        future_1 = asyncio.ensure_future(get('key_2'))
        result = await future_1
    return result

async def control_flow_dep_inside():
    """
    Check that dependent results used inside a control flow are awaited
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

async def control_flow_transform_inside():
    """
    Check that invocations produced inside a control flow are awaited inside the control flow
    """
    temp = placeholder_code()
    if temp:
        placeholder_code()
        future_0 = asyncio.ensure_future(get('key'))
        x = await future_0
        placeholder_code()
    else:
        placeholder_code()
        future_1 = asyncio.ensure_future(get('key'))
        x = await future_1
        placeholder_code()
    return result

async def control_flows_dep():
    """
    Check control flow dependency with for, while, if statements
    """
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

async def control_flows_dep_in_control():
    """
    Check control flow dependency with dependency inside the control statement
    """
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

async def control_flow_externalizing_order():
    """
    Check that invocations produced inside a control flow are awaited inside the control flow
    """
    temp = placeholder_code()
    if temp:
        placeholder_code()
        future_0 = asyncio.ensure_future(get('key'))
        x = await future_0
        send_user_message()
        future_1 = asyncio.ensure_future(get('key'))
        z = await future_1
        placeholder_code()
    else:
        placeholder_code()
        future_2 = asyncio.ensure_future(get('key'))
        x = await future_2
        placeholder_code()
    return result

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

async def function_for():
    future_0 = asyncio.ensure_future(get('key'))
    async_iter_0 = await future_0
    for element in async_iter_0:
        placeholder_code()
    return True

async def function_as_while():
    future_0 = asyncio.ensure_future(get('key'))
    async_cond_0 = await future_0
    while async_cond_0:
        placeholder_code()
    return True

@decorator
def send_user_message(message):
    print(f'User message: {message}')