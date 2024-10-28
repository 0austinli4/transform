# transform

Python program transformer that changes a program from synchronous to async. The transformation does this by creating tasks (using python's asyncio `ensure_future`) call. 

It makes the following guarantees: 
- Function call invocation order will always be in the same order as original program
- External facing messages (decided by user through decorators) will always be same order as original program
- Invocations will we brought as early as possible with respect to each function definition, and awaits will be used as late as possible
- All calls within a method will terminate before returning that method

# To run the application

1] create a list of functions you want to make asychronouos (you must include all functions that call these methods as well). 

2] mark any external client facing messages with a decorator function

Call `python main.py [path_to_file] {'functions to make async'}`

Example of the expected input/output or a use case:

Command: `python main.py program.py 'basic_test, get'`

Original program:
```
def basic_test():
    placeholder_code()
    x = get('key')
    placeholder_code()
    return result
```
Transformed program:
```
async def basic_test():
    future_0 = asyncio.ensure_future(get('key'))
    placeholder_code()
    placeholder_code()
    x = await future_0
    return result
```
Note that the original function call is turned into a python asyncio task, and the await is called right before the method returns. 
