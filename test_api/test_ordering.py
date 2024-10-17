
def test():
    # # async -> sync not dependent
    res_1 = get(l)
    abc = process_true()
    if a:
        if res_1:
            print("hello")
    res_2 = random_op(abc)
    send_user_message()

    # # two async operations dependent
    z = get(x)
    y = get(z)
    print("random")
    send_user_message(message)
    
    # async -> sync dependent
    var_res = get(var)
    second_res = random_op(var_res)

    send_user_message(message)

    # sync dependent -> async dependent , shouldn't be pushed above 
    z = random_op(x)
    p = random_op(x)
    y = get(z)

    send_user_message(message)
    
    # sync dependent -> async dependent -> sync dependent, shouldn't be pushed above 
    z = random_op(x)
    y = get(z)
    m = get(y)

    return True


@decorator
def send_user_message(message):
    print(f"User message: {message}")
