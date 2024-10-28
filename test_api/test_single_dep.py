def test():
    '''
    Check that dependent results used inside a control flow are awaited
    '''
    x = get('key')
    
    # await should be inside of the if statements
    if temp:
        result = get(x)
    else:
        get('key_2')
    if result:
        return result
    return ' '