import asyncio

async def basic_test_control_flow():
    """
    Check that awaits and invocations can move past control flow statements
    """
    if placeholder_code():
        placeholder_code()
    future_0 = asyncio.ensure_future(get('key'))
    y = await future_0
    return True