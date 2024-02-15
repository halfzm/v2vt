import time


def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print(f"{func.__name__} 运行时间为：{run_time:.4f} 秒")
        return result

    return wrapper
