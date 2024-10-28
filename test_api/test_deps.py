'''
Test file for program transformations

Async operations: 
    - GET 

Sync operations:
    - SYNC_OP
    - placeholder_code()

placeholder_code() represents any sequence of code that is not involved in the transformation 
i.e., not dependent code or an async calls. Invocations and responses can freely move
between these portions of code

send_user_message() represents an externalized function (defined via decoration). Invocations and
responses should be restricted by the location of these statements. 

'''
### Basic tests
def basic_test():
    '''
    Test that awaits are pushed to bottom, and invocations are pushed to top
    '''
    placeholder_code()
    x = get('key')
    placeholder_code()
    return result

### TESTS FOR DEPENDENCIES
def basic_test_dep_await():
    '''
    Test that awaits only get pushed down until dependency
    '''
    x = get('key')
    placeholder_code()
    result = sync_op(x)
    return result

def basic_test_dep_invoke():
    '''
    Test that async invocation only get pushed up until production of dependent variable
    '''
    x = sync_op('key')
    placeholder_code()
    result = get(x)
    return result

def basic_test_dep_asyncs():
    '''
    Test that async invocation only get pushed up until 
    production of dependent variable with another async
    '''
    y = get('key')
    placeholder_code()
    result = get(y)
    return result

def basic_test_externalizing_order():
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

### TEST FOR CONTROL FLOW / IF STATEMENTS
def basic_test_control_flow():
    '''
    Check that awaits and invocations can move past control flow statements
    '''
    if placeholder_code():
        placeholder_code()
    
    y = get('key')

    if res:
        placeholder_code()
    
    return True


def control_flow_dep_comparator():
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

def control_flow_dep_inside():
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

def control_flow_transform_inside():
    '''
    Check that invocations produced inside a control flow are awaited inside the control flow
    '''
    temp = placeholder_code()

    if temp:
        placeholder_code()
        x = get('key')
        placeholder_code()
    else:
        placeholder_code()
        x = get('key')
        placeholder_code()
    return result

def control_flows_dep():
    '''
    Check control flow dependency with for, while, if statements
    '''
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

def control_flows_dep_in_control():
    '''
    Check control flow dependency with dependency inside the control statement
    '''
    placeholder_code()
    x = get('key')
    while True:
        placeholder_code(x)
    z = get('key')
    for element in list:
        placeholder_code(z)
    return True

def control_flows_invocation():
    '''
    Check control flow dependency with dependency inside the control statement
    '''

    placeholder_code()
    x = placeholder_code()
    if placeholder_code():
        x = new_code()
    result = get(x)
    return result


def control_flow_externalizing_order():
    '''
    Check that invocations produced inside a control flow are awaited inside the control flow
    '''
    temp = placeholder_code()

    if temp:
        placeholder_code()
        x = get('key')
        send_user_message()
        z = get('key')
        placeholder_code()
    else:
        placeholder_code()
        x = get('key')
        placeholder_code()
    return result


### INVOCATION ORDER TESTS
        
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
    
def invocation_order_inside_tests():
    '''
    Check other types of tests(deps) when placing between external invocations
    '''
    send_user_message()
    if placeholder_code():
        placeholder_code()
    
    y = get('key')

    if res:
        placeholder_code()
    
    send_user_message()
    
    placeholder_code(x)
    
    send_user_message()

    x = get('key')
    result = None
    if x:
        placeholder_code()
    else:
        result = get('key_2')
        return result
    
    send_user_message()

    return True

### Function definitions that transformation must add assignments for
        
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

def function_as_while():
    while get('key'):
        placeholder_code()
    return True

### Check that functions consistency is correct
        
def consistency_res():
    '''
    two results are named the same  - make sure both are awaited
    '''
    x = get('key')    
    x = get('key')
    
    return True

### Check multiple variables can be assigned as inputs and ouptuts to functions
def consistency_res():
    '''
    two results are named the same  - make sure both are awaited
    '''
    x, y = get('key')   
    placeholder_code(x)
    
    return True

@decorator
def send_user_message(message):
    print(f"User message: {message}")
