"""Launch and control kernels using asyncio.
"""
from abc import ABC, abstractmethod
# noinspection PyCompatibility
import asyncio

from .launcher2 import make_connection_file, build_popen_kwargs

class AsyncKernelLauncher(ABC):
    """Interface for async kernel launchers.

    This is very similar to the KernelLauncher interface, but its methods
    are asyncio coroutines. There is no poll method, but you can get a future
    from the wait method and then poll it by checking ``future.done()``.
    """
    @abstractmethod
    def wait(self):
        """Wait for the kernel process to exit.
        """
        raise NotImplementedError()

    @abstractmethod
    def send_signal(self, signum):
        """Send a signal to the kernel."""
        pass

    def cleanup(self):
        """Clean up any resources."""
        pass

    @abstractmethod
    def get_connection_info(self):
        """Return a dictionary of connection information"""
        pass


# noinspection PyCompatibility
class AsyncPopenKernelLauncher(AsyncKernelLauncher):
    """Launch a kernel asynchronously in a subprocess.

    This is the async counterpart to PopenKernelLauncher.
    """
    process = None
    connection_file = None
    connection_info = None

    def __init__(self, process, connection_file, connection_info):
        self.process = process
        self.connection_file = connection_file
        self.connection_info = connection_info

    # __init__ can't be async, so this is the preferred constructor:
    @classmethod
    @asyncio.coroutine
    def launch(cls, cmd_template, extra_env, cwd):
        connection_file, connection_info = make_connection_file()
        kwargs = build_popen_kwargs(cmd_template, connection_file,
                                    extra_env, cwd)
        args = kwargs.pop('args')
        p = yield from asyncio.create_subprocess_exec(*args, **kwargs)
        return cls(p, connection_file, connection_info)

    @asyncio.coroutine
    def wait(self):
        return (yield from self.process.wait())

    @asyncio.coroutine
    def send_signal(self, signum):
        return self.process.send_signal(signum)

    @asyncio.coroutine
    def cleanup(self):
        super().cleanup()

    @asyncio.coroutine
    def get_connection_info(self):
        return self.connection_info


# noinspection PyCompatibility
class AsyncLauncherWrapper(AsyncKernelLauncher):
    """Wrap a blocking KernelLauncher to be used asynchronously.

    This calls the blocking methods in the event loop's default executor.
    """
    def __init__(self, wrapped, loop=None):
        self.wrapped = wrapped
        self.loop = loop or asyncio.get_event_loop()

    def in_default_executor(self, f, *args):
        return self.loop.run_in_executor(None, f, *args)

    @asyncio.coroutine
    def launch(self):
        return (yield from self.in_default_executor(self.wrapped.launch))

    @asyncio.coroutine
    def wait(self):
        return (yield from self.in_default_executor(self.wrapped.wait))

    @asyncio.coroutine
    def send_signal(self, signum):
        return (yield from self.in_default_executor(self.wrapped.send_signal, signum))

    @asyncio.coroutine
    def cleanup(self):
        return (yield from self.in_default_executor(self.wrapped.cleanup))

    @asyncio.coroutine
    def get_connection_info(self):
        return (yield from self.in_default_executor(self.wrapped.get_connection_info))
