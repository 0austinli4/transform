import asyncio

def init_redis():
    pending_awaits = {*()}
    future_0 = asyncio.ensure_future(redis_client.exists('total_users'))
    pending_awaits.add(future_0)
    total_users_exist = await future_0
    pending_awaits.remove(future_0)
    if not total_users_exist:
        future_1 = asyncio.ensure_future(redis_client.set('total_users', 0))
        pending_awaits.add(future_1)
        future_2 = asyncio.ensure_future(redis_client.set(f'room:0:name', 'General'))
        pending_awaits.add(future_2)
        demo_data.create()
    return (pending_awaits, None)