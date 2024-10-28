def test():
    '''
    Check that dependent results used inside a comparison
    '''
    x = get('key')
    result = None
    if x:
        placeholder_code()
    else:
        result = get('key_2')
        return result
    return result