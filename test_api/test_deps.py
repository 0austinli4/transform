'''
Test file for IOC ordering 

Async operations: GET 

Sync operations: SYNC_OP

placeholder_code() represents any sequence of code that is not involved in the transformation 
i.e., not dependent, not sychronous or async calls. Invocations and responses can freely move
between these portions of code

send_user_message() represents an externalized function (with decoration). Invocations and
responses should be restricted by the location of these statements. 
'''

def basic_test():
    '''
    Test that awaits are pushed to bottom, and invocations are pushed to top
    '''
    placeholder_code()
    x = get('key')
    placeholder_code()
    return result

def simple_dep_async_sync():
    '''
    Test that awaits only get pushed down until dependency
    '''
    x = get('key')
    placeholder_code()
    result = sync_op(x)
    return result

def simple_dep_sync_async():
    '''
    Test that async invocation only get pushed up until production of dependent variable
    '''
    x = sync_op('key')
    placeholder_code()
    result = get(x)
    return result

def simple_dep_async_async():
    '''
    Test that async invocation only get pushed up until 
    production of dependent variable with another async
    '''
    y = get('key')
    placeholder_code()
    result = get(y)
    return result

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

def control_flow_simple():
    '''
    Check that invocations produced inside a control flow are awaited inside the control flow
    '''
    temp = placeholder_code()

    if temp:
        x = get('key')
    else:
        x = get('key_2')
    return result

def control_flow_dep_result():
    '''
    Check that dependent results produced inside a control flow are awaited
    '''
    x = get('key')

    if temp:
        result = get(x)
    else:
        result = get('key_2')
    return result

def control_flow_dep_simple():
    '''
    Check that a response used inside a control flow is awaited outside of that contorl flow
    '''
    y = get('key')
    res = placeholder_code()
    
    if res:
        placeholder_code(y)
    
    return True

def control_flows_dep():
    y = get('key')
    if y:
        placeholder_code()
    x = get('key')
    placeholder_code()

    while x:
        placeholder_code()
    z = get('key')
    for element in z:
        placeholder_code()
    return True

def control_flows_dep_inside():
    placeholder_code()
    x = get('key')
    while True:
        placeholder_code(x)
    z = get('key')
    for element in list:
        placeholder_code(z)
    return True
    
def invocation_order_with_deps():
    '''
    Check that when two operations are awaited and second is used as dependency, 
    we pop out only the dependency and push the response (does not have to be
    in order)
    '''
    y = get('key')
    x = get('key')
    
    placeholder_code(x)
    
    return True

def function_def_without_result():
    get('key')    
    placeholder_code()
    placeholder_code()
    placeholder_code()
    
    return True

def function_as_if():
    if get('key'):
        placeholder_code()
    return True


def function_for():
    for element in get('key'):
        placeholder_code()
    return True

def function_as_if():
    '''
    Check that when two operations are awaited and second is used as dependency, 
    we pop out only the dependency and push the response (does not have to be
    in order)
    '''
    while get('key'):
        placeholder_code()
    return True

@decorator
def send_user_message(message):
    print(f"User message: {message}")
