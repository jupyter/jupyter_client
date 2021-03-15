import os
import sys
import asyncio
import inspect
import nest_asyncio

if os.name == 'nt' and sys.version_info >= (3, 7):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def run_sync(coro):
    def wrapped(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        nest_asyncio.apply(loop)
        return loop.run_until_complete(coro(*args, **kwargs))
    wrapped.__doc__ = coro.__doc__
    return wrapped

async def ensure_async(obj):
    if inspect.isawaitable(obj):
        return await obj
    return obj
