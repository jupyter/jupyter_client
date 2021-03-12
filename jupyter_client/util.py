import asyncio
import inspect
import nest_asyncio
nest_asyncio.apply()

loop = asyncio.get_event_loop()

def run_sync(coro):
    def wrapped(*args, **kwargs):
        return loop.run_until_complete(coro(*args, **kwargs))
    wrapped.__doc__ = coro.__doc__
    return wrapped

async def ensure_async(obj):
    if inspect.isawaitable(obj):
        return await obj
    return obj
