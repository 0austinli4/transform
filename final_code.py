import asyncio

async def basic_test():
    future_0 = asyncio.ensure_future(get('key'))
    placeholder_code()
    placeholder_code()
    x = await future_0
    return result

async def basic_test_dep_await():
    future_0 = asyncio.ensure_future(get('key'))
    placeholder_code()
    x = await future_0
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
    placeholder_code()
    result = await future_1
    return result

async def basic_test_externalizing_order():
    future_0 = asyncio.ensure_future(get('key'))
    placeholder_code()
    y = await future_0
    send_user_message()
    future_1 = asyncio.ensure_future(get(y))
    placeholder_code()
    placeholder_code()
    z = await future_1

async def basic_test_control_flow():
    future_0 = asyncio.ensure_future(get('key'))
    if placeholder_code():
        placeholder_code()
    if res:
        placeholder_code(y)
    y = await future_0
    return True

async def control_flow_dep_comparator():
    future_0 = asyncio.ensure_future(get('key'))
    if x:
        placeholder_code()
    else:
        future_1 = asyncio.ensure_future(get('key_2'))
        result = await future_1
    x = await future_0
    return result

async def control_flow_dep_inside():
    future_0 = asyncio.ensure_future(get('key'))
    if temp:
        future_1 = asyncio.ensure_future(get(x))
        result = await future_1
    else:
        future_2 = asyncio.ensure_future(get('key_2'))
        result = await future_2
    x = await future_0
    return result

async def control_flow_transform_inside():
    """
    Check that invocations produced inside a control flow are awaited inside the control flow
    """
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
    future_0 = asyncio.ensure_future(get('key'))
    future_1 = asyncio.ensure_future(get('key'))
    future_2 = asyncio.ensure_future(get('key'))
    if y:
        placeholder_code()
    placeholder_code()
    x = await future_1
    while x:
        placeholder_code()
    z = await future_2
    for element in z:
        placeholder_code()
    y = await future_0
    return True

async def control_flows_dep_in_control():
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

async def control_flow_externalizing_order():
    """
    Check that invocations produced inside a control flow are awaited inside the control flow
    """
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
    future_0 = asyncio.ensure_future(get('key'))
    future_1 = asyncio.ensure_future(get('key'))
    x = await future_1
    placeholder_code(x)
    y = await future_0
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
    if async_cond_0:
        placeholder_code()
    async_cond_0 = await future_0
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