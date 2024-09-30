from api_async import User

import asyncio


async def test_Function():
    api = User() 
    name = api.get_name(42)


    await name
    print(name)

# async def main():

