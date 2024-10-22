import asyncio
import time

async def async_task(task_id, delay):
    print(f"Task {task_id} started")
    await asyncio.sleep(delay)
    print(f"Task {task_id} completed")
    return f"Result from task {task_id}"

def sync_task(task_id, delay):
    print(f"Task {task_id} started")
    time.sleep(delay)
    print(f"Task {task_id} completed")
    return f"Result from task {task_id}"

async def run_async_tasks():
    f1 = asyncio.ensure_future(async_task(1, 3))
    f2 = asyncio.ensure_future(async_task(2, 3))
    f3 = asyncio.ensure_future(async_task(3, 3))

    start_time = time.perf_counter_ns()
    x = await f3
    end_time = time.perf_counter_ns()
    print(f"Time to wait for f3 first time {end_time - start_time}")

    times = []
    for i in range(100000):
        start_time = time.perf_counter_ns()
        x = await f3
        end_time = time.perf_counter_ns()
        times.append(end_time - start_time)
    total_time = sum(times)
    print(f"Time to wait for f3 average time", total_time/100000)
    

def run_sync_tasks():
    f1 = sync_task(1, 2)
    f2 = sync_task(2, 1)
    f3 = sync_task(3, 3)

if __name__ == "__main__":
    print("Running asynchronous tasks:")
    start_time = time.time()
    asyncio.run(run_async_tasks())
    end_time = time.time()
    print(f"Async tasks completed in {end_time - start_time:.2f} seconds")