import concurrent.futures
import asyncio

def asyncio_run(task):
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(task)

def run_sync(coro):
    def wrapped(*args, **kwargs):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio_run, coro(*args, **kwargs))
        return future.result()
    wrapped.__doc__ = coro.__doc__
    return wrapped
