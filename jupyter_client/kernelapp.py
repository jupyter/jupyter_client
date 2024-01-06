"""An application to launch a kernel by name in a local subprocess."""
import asyncio
import functools
import os
import signal
import typing as t
import uuid

from jupyter_core.application import JupyterAsyncApp, base_flags
from traitlets import Unicode

from . import __version__
from .kernelspec import NATIVE_KERNEL_NAME, KernelSpecManager
from .manager import AsyncKernelManager


class KernelApp(JupyterAsyncApp):
    """Launch a kernel by name in a local subprocess."""

    version = __version__
    description = "Run a kernel locally in a subprocess"

    classes = [AsyncKernelManager, KernelSpecManager]

    aliases = {
        "kernel": "KernelApp.kernel_name",
        "ip": "KernelManager.ip",
    }
    flags = {"debug": base_flags["debug"]}

    kernel_name = Unicode(NATIVE_KERNEL_NAME, help="The name of a kernel type to start").tag(
        config=True
    )

    async def initialize_async(self, argv: t.Union[str, t.Sequence[str], None] = None) -> None:
        """Initialize the application."""
        super().initialize(argv)

        cf_basename = "kernel-%s.json" % uuid.uuid4()
        self.config.setdefault("KernelManager", {}).setdefault(
            "connection_file", os.path.join(self.runtime_dir, cf_basename)
        )
        self.km = AsyncKernelManager(kernel_name=self.kernel_name, config=self.config)
        await self._record_started()
        self._stopped_fut: asyncio.Future[int] = asyncio.Future()
        self._running = None

    def setup_signals(self) -> None:
        """Shutdown on SIGTERM or SIGINT (Ctrl-C)"""
        if os.name == "nt":
            return

        loop = asyncio.get_running_loop()
        for signo in [signal.SIGTERM, signal.SIGINT]:
            loop.add_signal_handler(signo, functools.partial(self.shutdown, signo))

    def shutdown(self, signo: int) -> None:
        """Shut down the application."""
        self._stopped_fut.set_result(signo)

    def log_connection_info(self) -> None:
        """Log the connection info for the kernel."""
        cf = self.km.connection_file
        self.log.info("Connection file: %s", cf)
        self.log.info("To connect a client: --existing %s", os.path.basename(cf))

    def _record_started(self) -> None:
        """For tests, create a file to indicate that we've started

        Do not rely on this except in our own tests!
        """
        fn = os.environ.get("JUPYTER_CLIENT_TEST_RECORD_STARTUP_PRIVATE")
        if fn is not None:
            with open(fn, "wb"):
                pass

    async def start_async(self) -> None:
        self.log.info("Starting kernel %r", self.kernel_name)
        km = self.km
        try:
            self.setup_signals()
            self.log_connection_info()
            await km.start_kernel()
            stopped_sig = await self._stopped_fut
            self.log.info("Shutting down on signal %d", stopped_sig)
            await km.shutdown_kernel()
        finally:
            await km.cleanup_resources()


main = KernelApp.launch_instance
