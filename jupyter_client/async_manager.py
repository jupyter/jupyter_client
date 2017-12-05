"""Launch and control kernels using asyncio.
"""
# noinspection PyCompatibility
import asyncio
import os

from .launcher2 import make_connection_file, build_popen_kwargs
from .localinterfaces import is_local_ip, local_ips
from .manager2 import KernelManager2, KernelManager2ABC

# noinspection PyCompatibility
class AsyncPopenKernelManager(KernelManager2):
    """Run a kernel asynchronously in a subprocess.

    This is the async counterpart to PopenKernelLauncher.
    """
    _exit_future = None

    @asyncio.coroutine
    def start_kernel(self):
        if self.transport == 'tcp' and not is_local_ip(self.ip):
            raise RuntimeError("Can only launch a kernel on a local interface. "
                               "Make sure that the '*_address' attributes are "
                               "configured properly. "
                               "Currently valid addresses are: %s" % local_ips()
                               )

        self.connection_file, self.connection_info = \
            make_connection_file(self.ip, self.transport)

        kw = build_popen_kwargs(self.kernel_cmd, self.connection_file,
                                self.extra_env, self.cwd)

        # launch the kernel subprocess
        args = kw.pop('args')
        self.log.debug("Starting kernel: %s", args)
        self.kernel = yield from asyncio.create_subprocess_exec(*args, **kw)
        self._exit_future = asyncio.ensure_future(self.kernel.wait())

    @asyncio.coroutine
    def wait(self, timeout):
        try:
            yield from asyncio.wait_for(self.kernel.wait(), timeout)
            return False
        except asyncio.TimeoutError:
            return True

    @asyncio.coroutine
    def is_alive(self):
        return not (self._exit_future and self._exit_future.done())

    @asyncio.coroutine
    def signal(self, signum):
        return self.kernel.send_signal(signum)

    @asyncio.coroutine
    def interrupt(self):
        return super().interrupt()

    @asyncio.coroutine
    def kill(self):
        return self.kernel.kill()

    @asyncio.coroutine
    def cleanup(self):
        return super().cleanup()

    @asyncio.coroutine
    def get_connection_info(self):
        return super().get_connection_info()

# noinspection PyCompatibility
@asyncio.coroutine
def shutdown(client, manager, wait_time=5.0):
    """Shutdown a kernel using a client and a manager.

    Attempts a clean shutdown by sending a shutdown message. If the kernel
    hasn't exited in wait_time seconds, it will be killed. Set wait_time=None
    to wait indefinitely.
    """
    client.shutdown()
    if (yield from manager.wait(wait_time)):
        # OK, we've waited long enough.
        manager.log.debug("Kernel is taking too long to finish, killing")
        manager.kill()
    manager.cleanup()

# noinspection PyCompatibility
@asyncio.coroutine
def start_new_kernel(kernel_cmd, startup_timeout=60, cwd=None):
    """Start a new kernel, and return its Manager and a blocking client"""
    from .client2 import BlockingKernelClient2
    cwd = cwd or os.getcwd()

    km = AsyncPopenKernelManager(kernel_cmd, cwd=cwd)
    yield from km.start_kernel()
    # TODO: asyncio client
    kc = BlockingKernelClient2(km.connection_info, manager=km)
    try:
        kc.wait_for_ready(timeout=startup_timeout)
    except RuntimeError:
        yield from shutdown(kc, km)
        raise

    return km, kc

# noinspection PyCompatibility
class AsyncLauncherWrapper(KernelManager2ABC):
    """Wrap a blocking KernelLauncher to be used asynchronously.

    This calls the blocking methods in the event loop's default executor.
    """
    def __init__(self, wrapped, loop=None):
        self.wrapped = wrapped
        self.loop = loop or asyncio.get_event_loop()

    def in_default_executor(self, f, *args):
        return self.loop.run_in_executor(None, f, *args)

    @asyncio.coroutine
    def is_alive(self):
        return (yield from self.in_default_executor(self.wrapped.is_alive))

    @asyncio.coroutine
    def wait(self, timeout):
        return (yield from self.in_default_executor(self.wrapped.wait, timeout))

    @asyncio.coroutine
    def signal(self, signum):
        return (yield from self.in_default_executor(self.wrapped.signal, signum))

    @asyncio.coroutine
    def interrupt(self):
        return (yield from self.in_default_executor(self.wrapped.interrupt))

    @asyncio.coroutine
    def kill(self):
        return (yield from self.in_default_executor(self.wrapped.kill))

    @asyncio.coroutine
    def cleanup(self):
        return (yield from self.in_default_executor(self.wrapped.cleanup))

    @asyncio.coroutine
    def get_connection_info(self):
        return (yield from self.in_default_executor(self.wrapped.get_connection_info))
