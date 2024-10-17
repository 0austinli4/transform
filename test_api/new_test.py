
### SIMPLE TESTS
# Order of data-dependent actions
def test_data_dependency_down():
    result = get('x')
    print("hello")
    processed = process(result)
    return processed

# R1:Order of data-dependent actions
def test_data_dependency_up():
    # this is not a async function
    processed = get_name()
    # this is
    result = get(processed)
    print("hello")
    return processed

# R2: Control flow
def test_control_flow():
    condition = get_condition()
    if condition:
        step1()
        step2()
        result = process_true()
    else:
        step1()
        step2()
        result = process_false()
    return result

# R3: Invocation order
def test_invocation_order():
    step1()
    step2()
    step3()
    return "Done"

# R4: the order of non-system-facing external actions in A, including messages to/from users
def test_external():
    send_user_message("Starting")
    process_data()
    send_user_message("Finished")
    return "Complete"

# R5: the order between a non-system-facing external
# actions and operation invocations (in particular, the first
# invocation in a sequence of operations), and
def test_external_and_invocation():
    send_user_message("Beginning operation") # future can not be pushed above this line
    result = perform_operation()
    return result

# R6: Order between external actions and operation responses
def test_external_and_response():
    long_operation1() #async
    long_operation2() #async
    send_user_message("All operations complete")  # await can not be pushed below this line
    processed = get_name() #async
    return "Finished"

### MORE COMPLEX TESTS

def async_creation_within_control_flow():
    if not get():
        return False
    for item in other_function():
        print(item)
    while process_true():
        print("Processing true")
    return True

def data_dependency_inside_control_flow():
    a = 2
    result = get('x')

    if a == 2:
        processed = process(result)
    else:
        print("Other operation")
    return processed

def external_inside_control_flow():
    a = 0
    result = get('x')
    
    if a == 0:
        send_user_message("All operations complete")  # await can not be pushed below this line
    else:
        print("Other operation")
    return processed








# # Helper functions
# def get(item):
#     return f"Data for {item}"

# def process(data):
#     return f"Processed {data}"

# def get_condition():
#     return True

# def process_true():
#     return "Condition was true"

# def process_false():
#     return "Condition was false"

# def step1():
#     print("Step 1")

# def step2():
#     print("Step 2")

# def step3():
#     print("Step 3")

@decorator
def send_user_message(message):
    print(f"User message: {message}")

# def process_data():
#     print("Processing data")

# def perform_operation():
#     return "Operation result"

# def long_operation1():
#     # Simulating a long operation
#     import time
#     time.sleep(1)
#     return "Operation 1 complete"

# def long_operation2():
#     # Simulating another long operation
#     import time
#     time.sleep(1)
#     return "Operation 2 complete"
