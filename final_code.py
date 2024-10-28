import asyncio
'\nTest file for program transformations\n\nAsync operations: \n    - GET \n\nSync operations:\n    - SYNC_OP\n    - placeholder_code()\n\nplaceholder_code() represents any sequence of code that is not involved in the transformation \ni.e., not dependent code or an async calls. Invocations and responses can freely move\nbetween these portions of code\n\nsend_user_message() represents an externalized function (defined via decoration). Invocations and\nresponses should be restricted by the location of these statements. \n\n'

async def basic_test():
    """Test that awaits are pushed to bottom, and invocations are pushed to top"""
    future_0 = asyncio.ensure_future(get('key'))
    placeholder_code()
    placeholder_code()
    x = await future_0
    return result

async def basic_test_dep_await():
    """Test that awaits only get pushed down until dependency"""
    future_0 = asyncio.ensure_future(get('key'))
    placeholder_code()
    x = await future_0
    result = sync_op(x)
    return result

async def basic_test_dep_invoke():
    """Test that async invocation only get pushed up until production of dependent variable"""
    x = sync_op('key')
    future_0 = asyncio.ensure_future(get(x))
    placeholder_code()
    result = await future_0
    return result

async def basic_test_dep_asyncs():
    """Test that async invocation only get pushed up until 
production of dependent variable with another async"""
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    future_1 = asyncio.ensure_future(get(y))
    placeholder_code()
    result = await future_1
    return result

async def basic_test_externalizing_order():
    """Test ordering with external functions"""
    future_0 = asyncio.ensure_future(get('key'))
    placeholder_code()
    y = await future_0
    send_user_message()
    future_1 = asyncio.ensure_future(get(y))
    placeholder_code()
    placeholder_code()
    z = await future_1

async def basic_test_control_flow():
    """Check that awaits and invocations can move past control flow statements"""
    future_0 = asyncio.ensure_future(get('key'))
    if placeholder_code():
        placeholder_code()
    if res:
        placeholder_code()
    y = await future_0
    return True

async def control_flow_dep_comparator():
    """Check that dependent results used inside a comparison"""
    future_0 = asyncio.ensure_future(get('key'))
    result = None
    x = await future_0
    if x:
        placeholder_code()
    else:
        future_1 = asyncio.ensure_future(get('key_2'))
        result = await future_1
    return result

async def control_flow_dep_inside():
    """Check that dependent results used inside a control flow are awaited"""
    future_0 = asyncio.ensure_future(get('key'))
    if temp:
        x = await future_0
        future_1 = asyncio.ensure_future(get(x))
        result = await future_1
    else:
        future_2 = asyncio.ensure_future(get('key_2'))
        await future_2
    if result:
        x = await future_0
        return result
    x = await future_0
    return ' '

async def control_flow_transform_inside():
    """Check that invocations produced inside a control flow are awaited inside the control flow"""
    temp = placeholder_code()
    if temp:
        future_0 = asyncio.ensure_future(get('key'))
        placeholder_code()
        placeholder_code()
        x = await future_0
    else:
        future_1 = asyncio.ensure_future(get('key'))
        placeholder_code()
        placeholder_code()
        x = await future_1
    return result

async def control_flows_dep():
    """Check control flow dependency with for, while, if statements"""
    future_0 = asyncio.ensure_future(get('key'))
    future_1 = asyncio.ensure_future(get('key'))
    future_2 = asyncio.ensure_future(get('key'))
    y = await future_0
    if y:
        placeholder_code()
    placeholder_code()
    x = await future_1
    while x:
        placeholder_code()
    z = await future_2
    for element in z:
        placeholder_code()
    return True

async def control_flows_dep_in_control():
    """Check control flow dependency with dependency inside the control statement"""
    future_0 = asyncio.ensure_future(get('key'))
    future_1 = asyncio.ensure_future(get('key'))
    placeholder_code()
    x = await future_0
    while True:
        placeholder_code(x)
    z = await future_1
    for element in list:
        placeholder_code(z)
    return True

async def control_flows_invocation():
    """Check control flow dependency with dependency inside the control statement"""
    placeholder_code()
    x = placeholder_code()
    if placeholder_code():
        x = new_code()
    future_0 = asyncio.ensure_future(get(x))
    result = await future_0
    return result

async def control_flow_externalizing_order():
    """Check that invocations produced inside a control flow are awaited inside the control flow"""
    temp = placeholder_code()
    if temp:
        future_0 = asyncio.ensure_future(get('key'))
        placeholder_code()
        x = await future_0
        send_user_message()
        future_1 = asyncio.ensure_future(get('key'))
        placeholder_code()
        z = await future_1
    else:
        future_2 = asyncio.ensure_future(get('key'))
        placeholder_code()
        placeholder_code()
        x = await future_2
    return result

async def invocation_order_with_deps():
    """Check that when two operations are awaited and second is used as dependency, 
we pop out only the dependency and push the response (does not have to be
in order)"""
    future_0 = asyncio.ensure_future(get('key'))
    future_1 = asyncio.ensure_future(get('key'))
    x = await future_1
    placeholder_code(x)
    y = await future_0
    return True

async def invocation_order_inside_tests():
    """Check other types of tests(deps) when placing between external invocations"""
    send_user_message()
    future_0 = asyncio.ensure_future(get('key'))
    if placeholder_code():
        placeholder_code()
    if res:
        placeholder_code()
    y = await future_0
    send_user_message()
    placeholder_code(x)
    send_user_message()
    future_1 = asyncio.ensure_future(get('key'))
    result = None
    x = await future_1
    if x:
        placeholder_code()
    else:
        future_2 = asyncio.ensure_future(get('key_2'))
        result = await future_2
        x = await future_1
        return result
    send_user_message()
    return True

async def function_def_without_result():
    future_0 = asyncio.ensure_future(get('key'))
    placeholder_code()
    placeholder_code()
    placeholder_code()
    await future_0
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

def consistency_res():
    """
    two results are named the same  - make sure both are awaited
    """
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    future_1 = asyncio.ensure_future(get('key'))
    x = await future_1
    return True

@decorator
def send_user_message(message):
    print(f'User message: {message}')