import asyncio

def init_redis():
    future_0 = asyncio.ensure_future(redis_client.exists('total_users'))
    total_users_exist = await future_0
    if not total_users_exist:
        future_1 = asyncio.ensure_future(redis_client.set('total_users', 0))
        await future_1
        future_2 = asyncio.ensure_future(redis_client.set(f'room:0:name', 'General'))
        await future_2
        demo_data.create()