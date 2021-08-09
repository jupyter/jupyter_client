import asyncio
import gc
import os
import sys

import pytest
import zmq
from jupyter_core import paths
from zmq.tests import BaseZMQTestCase

from .utils import test_env

pjoin = os.path.join


if os.name == "nt" and sys.version_info >= (3, 7):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture
def event_loop():
    # Make sure we test against a selector event loop
    # since pyzmq doesn't like the proactor loop.
    # This fixture is picked up by pytest-asyncio
    if os.name == "nt" and sys.version_info >= (3, 7):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.SelectorEventLoop()
    try:
        yield loop
    finally:
        loop.close()


@pytest.fixture(autouse=True)
def env():
    env_patch = test_env()
    env_patch.start()
    yield
    env_patch.stop()


@pytest.fixture()
def kernel_dir():
    return pjoin(paths.jupyter_data_dir(), 'kernels')


def assert_no_zmq():
    """Verify that there are no zmq resources

    avoids reference leaks across tests,
    which can lead to FD exhaustion
    """
    # zmq garbage collection uses a zmq socket in a thread
    # we don't want to delete these from the main thread!
    from zmq.utils import garbage

    garbage.gc.stop()
    sockets = [
        obj
        for obj in gc.get_referrers(zmq.Socket)
        if isinstance(obj, zmq.Socket) and not obj.closed
    ]
    if sockets:
        message = f"{len(sockets)} unclosed sockets: {sockets}"
        for s in sockets:
            s.close(linger=0)
        raise AssertionError(message)
    contexts = [
        obj
        for obj in gc.get_referrers(zmq.Context)
        if isinstance(obj, zmq.Context) and not obj.closed
    ]
    # allow for single zmq.Context.instance()
    if contexts and len(contexts) > 1:
        message = f"{len(contexts)} unclosed contexts: {contexts}"
        for ctx in contexts:
            ctx.destroy(linger=0)
        raise AssertionError(message)


@pytest.fixture(autouse=True)
def check_zmq(request):
    yield
    if request.instance and isinstance(request.instance, BaseZMQTestCase):
        # can't run this check on old-style TestCases with tearDown methods
        # because this check runs before tearDown
        return
    assert_no_zmq()
