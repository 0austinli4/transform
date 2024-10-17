
def externalizing_order():
    '''
    Test ordering with external functions
    '''
    y = get('key')
    placeholder_code()
    ### externalizing function should create barrier between any await / async invocations
    send_user_message()
    placeholder_code()
    placeholder_code()
    z = get(y)

@decorator
def send_user_message():
    print("User message")