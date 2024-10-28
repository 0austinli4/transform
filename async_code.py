import asyncio

async def test():
    """
    Check that dependent results used inside a comparison
    """
    future_0 = asyncio.ensure_future(get('key'))
    x = await future_0
    result = None
    if x:
        placeholder_code()
    else:
        future_1 = asyncio.ensure_future(get('key_2'))
        result = await future_1
        return result
    return result