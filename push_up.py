import asyncio
'\nTest file for program transformations\n\nAsync operations: \n    - GET \n\nSync operations:\n    - SYNC_OP\n    - placeholder_code()\n\nplaceholder_code() represents any sequence of code that is not involved in the transformation \ni.e., not dependent code or an async calls. Invocations and responses can freely move\nbetween these portions of code\n\nsend_user_message() represents an externalized function (defined via decoration). Invocations and\nresponses should be restricted by the location of these statements. \n\n'

async def basic_test():
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    '\n    Test that awaits are pushed to bottom, and invocations are pushed to top\n    '
    placeholder_code()
    placeholder_code()
    return result

async def basic_test_dep_await():
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    '\n    Test that awaits only get pushed down until dependency\n    '
    placeholder_code()
    result = sync_op(x)
    return result

async def basic_test_dep_invoke():
    """
    Test that async invocation only get pushed up until production of dependent variable
    """
    x = sync_op('key')
    future_0 = asyncio.ensure_future(get(x))
    placeholder_code()
    result = await future_0
    return result

async def basic_test_dep_asyncs():
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    future_1 = asyncio.ensure_future(get(y))
    '\n    Test that async invocation only get pushed up until \n    production of dependent variable with another async\n    '
    placeholder_code()
    result = await future_1
    return result

async def basic_test_externalizing_order():
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    '\n    Test ordering with external functions\n    '
    placeholder_code()
    send_user_message()
    future_1 = asyncio.ensure_future(get(y))
    z = await future_1
    placeholder_code()
    placeholder_code()

async def basic_test_control_flow():
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    '\n    Check that awaits and invocations can move past control flow statements\n    '
    if placeholder_code():
        placeholder_code()
    if res:
        placeholder_code(y)
    return True

async def control_flow_dep_comparator():
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    '\n    Check that dependent results used inside a comparison\n    '
    if x:
        placeholder_code()
    else:
        future_1 = asyncio.ensure_future(get('key_2'))
        result = await future_1
    return result

async def control_flow_dep_inside():
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    '\n    Check that dependent results used inside a control flow are awaited\n    '
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
        future_0 = asyncio.ensure_future(get('key'))
        x = await future_0
        placeholder_code()
        placeholder_code()
    else:
        future_1 = asyncio.ensure_future(get('key'))
        x = await future_1
        placeholder_code()
        placeholder_code()
    return result

async def control_flows_dep():
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    future_1 = asyncio.ensure_future(get('key'))
    x = await future_1
    future_2 = asyncio.ensure_future(get('key'))
    z = await future_2
    '\n    Check control flow dependency with for, while, if statements\n    '
    if y:
        placeholder_code()
    placeholder_code()
    while x:
        placeholder_code()
    for element in z:
        placeholder_code()
    return True

async def control_flows_dep_in_control():
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    future_1 = asyncio.ensure_future(get('key'))
    z = await future_1
    '\n    Check control flow dependency with dependency inside the control statement\n    '
    placeholder_code()
    while True:
        placeholder_code(x)
    for element in list:
        placeholder_code(z)
    return True

async def control_flow_externalizing_order():
    """
    Check that invocations produced inside a control flow are awaited inside the control flow
    """
    temp = placeholder_code()
    if temp:
        future_0 = asyncio.ensure_future(get('key'))
        x = await future_0
        placeholder_code()
        send_user_message()
        future_1 = asyncio.ensure_future(get('key'))
        z = await future_1
        placeholder_code()
    else:
        future_2 = asyncio.ensure_future(get('key'))
        x = await future_2
        placeholder_code()
        placeholder_code()
    return result

async def invocation_order_with_deps():
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    future_1 = asyncio.ensure_future(get('key'))
    x = await future_1
    '\n    Check that when two operations are awaited and second is used as dependency, \n    we pop out only the dependency and push the response (does not have to be\n    in order)\n    '
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