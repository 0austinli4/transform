import time


def decorator(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result
    return wrapper

class MinStack:

    def __init__(self):
        self.stack = []
        self.min = []

    def push(self, val: int) -> None:
        self.network_delay()
        self.stack.append(val)
        if len(self.stack)==1:
            self.min.append(val)
        else:
            self.min.append(min(self.min[-1], val))
        
    def pop(self) -> None:
        self.network_delay()
        time.sleep(2)
        self.stack.pop()
        self.min.pop()

    def top(self) -> int:
        return self.stack[-1]
        

    def getMin(self) -> int:
        return self.min[-1]
    
    @decorator
    def network_delay(self) -> None:
        time.sleep(5)
        return 


# Your MinStack object will be instantiated and called as such:
def test():
    obj = MinStack()
    obj.push(1)
    obj.push(2)
    obj.push(3)
    obj.push(4)
    obj.pop()

t1 = time.perf_counter()
test()
t2 = time.perf_counter()
print("Total time", t2 - t1)
# param_3 = obj.top()
# param_4 = obj.getMin()