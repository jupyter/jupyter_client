"""Launch and control kernels using asyncio.
"""
from abc import ABC, abstractmethod
import asyncio

from .launcher2 import make_connection_file, build_popen_kwargs

class AsyncKernelLauncher(ABC):
    """Interface for async kernel launchers.

    This is very similar to the KernelLauncher interface, but its methods
    are coroutines.
    """
    @abstractmethod
    def launch(self):
        """Launch the kernel."""

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


class AsyncPopenKernelLauncher(AsyncKernelLauncher):
    """Launch a kernel asynchronously in a subprocess.

    This is the async counterpart to PopenKernelLauncher.
    """
    process = None
    connection_file = None
    connection_info = None

    def __init__(self, cmd_template, extra_env=None, cwd=None):
        self.cmd_template = cmd_template
        self.extra_env = extra_env
        self.cwd = cwd

    @asyncio.coroutine
    def launch(self):
        self.connection_file, self.connection_info = make_connection_file()
        kwargs = build_popen_kwargs(self.cmd_template, self.connection_file,
                                    self.extra_env, self.cwd)
        args = kwargs.pop('args')
        self.process = yield from asyncio.create_subprocess_exec(*args, **kwargs)

    @asyncio.coroutine
    def wait(self):
        return (yield from self.process.wait())

    @asyncio.coroutine
    def send_signal(self, signum):
        return self.process.send_signal(signum)

    @asyncio.coroutine
    def cleanup(self):
        super().cleanup()

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

