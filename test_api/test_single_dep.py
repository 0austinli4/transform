def init_redis():
    # We store a counter for the total users and increment it on each register
    total_users_exist = redis_client.exists("total_users")
    if not total_users_exist:
        # This counter is used for the id
        redis_client.set("total_users", 0)
        # Some rooms have pre-defined names. When the clients attempts to fetch a room, an additional lookup
        # is handled to resolve the name.
        # Rooms with private messages don't have a name
        redis_client.set(f"room:0:name", "General")

        demo_data.create()
