"""Launch and control kernels using asyncio.
"""
# noinspection PyCompatibility
import asyncio
import os

from traitlets.log import get_logger as get_app_logger

from .launcher2 import (
    make_connection_file, build_popen_kwargs, prepare_interrupt_event
)
from .localinterfaces import is_local_ip, local_ips, localhost
from .manager2 import KernelManager2, KernelManager2ABC
from .util import inherit_docstring

# noinspection PyCompatibility
class AsyncPopenKernelManager(KernelManager2):
    """Run a kernel asynchronously in a subprocess.

    This is the async counterpart to PopenKernelLauncher.
    After instantiating, call the launch() method to actually launch the
    subprocess. This is necessary because the constructor cannot be async.

    Parameters
    ----------

    kernel_cmd : list of str
      The Popen command template to launch the kernel
    cwd : str
      The working directory to launch the kernel in
    extra_env : dict, optional
      Dictionary of environment variables to update the existing environment
    ip : str, optional
      Set the kernel\'s IP address [default localhost].
      If the IP address is something other than localhost, then
      Consoles on other machines will be able to connect
      to the Kernel, so be careful!
    """
    _exit_future = None
    _win_interrupt_evt = None
    kernel = None

    def __init__(self, kernel_cmd, cwd, extra_env=None, ip=None):
        self.kernel_cmd = kernel_cmd
        self.cwd = cwd
        self.extra_env = extra_env
        if ip is None:
            ip = localhost()
        self.ip = ip
        self.log = get_app_logger()

        if self.transport == 'tcp' and not is_local_ip(ip):
            raise RuntimeError("Can only launch a kernel on a local interface. "
                               "Make sure that the '*_address' attributes are "
                               "configured properly. "
                               "Currently valid addresses are: %s" % local_ips()
                               )

        self.connection_file, self.connection_info = \
            make_connection_file(ip, self.transport)

    @asyncio.coroutine
    def launch(self):
        """Run this immediately after instantiation to launch the kernel process.
        """
        kw = build_popen_kwargs(self.kernel_cmd, self.connection_file,
                                self.extra_env, self.cwd)
        self._win_interrupt_evt = prepare_interrupt_event(kw['env'])

        # launch the kernel subprocess
        args = kw.pop('args')
        self.log.debug("Starting kernel: %s", args)
        self.kernel = yield from asyncio.create_subprocess_exec(*args, **kw)
        self.kernel.stdin.close()
        self._exit_future = asyncio.ensure_future(self.kernel.wait())

    @inherit_docstring(KernelManager2)
    @asyncio.coroutine
    def wait(self, timeout):
        try:
            yield from asyncio.wait_for(self.kernel.wait(), timeout)
            return False
        except asyncio.TimeoutError:
            return True

    @inherit_docstring(KernelManager2)
    @asyncio.coroutine
    def is_alive(self):
        return not self._exit_future.done()

    @inherit_docstring(KernelManager2)
    @asyncio.coroutine
    def signal(self, signum):
        return super().signal(signum)

    @inherit_docstring(KernelManager2)
    @asyncio.coroutine
    def interrupt(self):
        return super().interrupt()

    @inherit_docstring(KernelManager2)
    @asyncio.coroutine
    def kill(self):
        return super().kill()

    @inherit_docstring(KernelManager2)
    @asyncio.coroutine
    def cleanup(self):
        return super().cleanup()

    @inherit_docstring(KernelManager2)
    @asyncio.coroutine
    def get_connection_info(self):
        return self.connection_info

    @inherit_docstring(KernelManager2)
    @asyncio.coroutine
    def relaunch(self):
        kw = build_popen_kwargs(self.kernel_cmd, self.connection_file,
                                self.extra_env, self.cwd)
        prepare_interrupt_event(kw['env'], self._win_interrupt_evt)

        # launch the kernel subprocess
        args = kw.pop('args')
        self.log.debug("Starting kernel: %s", args)
        self.kernel = yield from asyncio.create_subprocess_exec(*args, **kw)
        self.kernel.stdin.close()
        self._exit_future = asyncio.ensure_future(self.kernel.wait())

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
    yield from km.launch()
    # TODO: asyncio client
    kc = BlockingKernelClient2(km.connection_info, manager=km)
    try:
        kc.wait_for_ready(timeout=startup_timeout)
    except RuntimeError:
        yield from shutdown(kc, km)
        raise

    return km, kc

# noinspection PyCompatibility
class AsyncManagerWrapper(KernelManager2ABC):
    """Wrap a blocking KernelLauncher to be used asynchronously.

    This calls the blocking methods in the event loop's default executor.
    """
    def __init__(self, wrapped, loop=None):
        self.wrapped = wrapped
        self.loop = loop or asyncio.get_event_loop()

    def _exec(self, f, *args):
        return self.loop.run_in_executor(None, f, *args)

    @asyncio.coroutine
    def is_alive(self):
        return (yield from self._exec(self.wrapped.is_alive))

    @asyncio.coroutine
    def wait(self, timeout):
        return (yield from self._exec(self.wrapped.wait, timeout))

    @asyncio.coroutine
    def signal(self, signum):
        return (yield from self._exec(self.wrapped.signal, signum))

    @asyncio.coroutine
    def interrupt(self):
        return (yield from self._exec(self.wrapped.interrupt))

    @asyncio.coroutine
    def kill(self):
        return (yield from self._exec(self.wrapped.kill))

    @asyncio.coroutine
    def cleanup(self):
        return (yield from self._exec(self.wrapped.cleanup))

    @asyncio.coroutine
    def get_connection_info(self):
        return (yield from self._exec(self.wrapped.get_connection_info))
