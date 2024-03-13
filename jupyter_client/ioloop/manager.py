"""A kernel manager with an asyncio IOLoop"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import asyncio
import typing as t

import zmq
import zmq.asyncio
from jupyter_core.utils import ensure_event_loop
from traitlets import Instance, Type
from zmq.eventloop.zmqstream import ZMQStream

from ..manager import AsyncKernelManager, KernelManager
from .restarter import AsyncIOLoopKernelRestarter, IOLoopKernelRestarter


def as_zmqstream(f: t.Any) -> t.Callable[..., ZMQStream]:
    """Convert a socket to a zmq stream."""

    def wrapped(self: t.Any, *args: t.Any, **kwargs: t.Any) -> t.Any:
        save_socket_class = None
        # zmqstreams only support sync sockets
        if self.context._socket_class is not zmq.Socket:
            save_socket_class = self.context._socket_class
            self.context._socket_class = zmq.Socket
        try:
            socket = f(self, *args, **kwargs)
        finally:
            if save_socket_class:
                # restore default socket class
                self.context._socket_class = save_socket_class
        return ZMQStream(socket)

    return wrapped


class IOLoopKernelManager(KernelManager):
    """An io loop kernel manager."""

    loop = Instance(asyncio.AbstractEventLoop)  # type:ignore[type-abstract]

    def _loop_default(self) -> asyncio.AbstractEventLoop:
        return ensure_event_loop()

    restarter_class = Type(
        default_value=IOLoopKernelRestarter,
        klass=IOLoopKernelRestarter,
        help=(
            "Type of KernelRestarter to use. "
            "Must be a subclass of IOLoopKernelRestarter.\n"
            "Override this to customize how kernel restarts are managed."
        ),
        config=True,
    )
    _restarter: t.Any = Instance("jupyter_client.ioloop.IOLoopKernelRestarter", allow_none=True)

    def start_restarter(self) -> None:
        """Start the restarter."""
        if self.autorestart and self.has_kernel:
            if self._restarter is None:
                self._restarter = self.restarter_class(
                    kernel_manager=self, parent=self, log=self.log
                )
            self._restarter.start()

    def stop_restarter(self) -> None:
        """Stop the restarter."""
        if self.autorestart and self._restarter is not None:
            self._restarter.stop()

    connect_shell = as_zmqstream(KernelManager.connect_shell)  # type:ignore[assignment]
    connect_control = as_zmqstream(KernelManager.connect_control)  # type:ignore[assignment]
    connect_iopub = as_zmqstream(KernelManager.connect_iopub)  # type:ignore[assignment]
    connect_stdin = as_zmqstream(KernelManager.connect_stdin)  # type:ignore[assignment]
    connect_hb = as_zmqstream(KernelManager.connect_hb)  # type:ignore[assignment]


class AsyncIOLoopKernelManager(AsyncKernelManager):
    """An async ioloop kernel manager."""

    loop = Instance(asyncio.AbstractEventLoop)  # type:ignore[type-abstract]

    def _loop_default(self) -> asyncio.AbstractEventLoop:
        return ensure_event_loop()

    restarter_class = Type(
        default_value=AsyncIOLoopKernelRestarter,
        klass=AsyncIOLoopKernelRestarter,
        help=(
            "Type of KernelRestarter to use. "
            "Must be a subclass of AsyncIOLoopKernelManager.\n"
            "Override this to customize how kernel restarts are managed."
        ),
        config=True,
    )
    _restarter: t.Any = Instance(
        "jupyter_client.ioloop.AsyncIOLoopKernelRestarter", allow_none=True
    )

    def start_restarter(self) -> None:
        """Start the restarter."""
        if self.autorestart and self.has_kernel:
            if self._restarter is None:
                self._restarter = self.restarter_class(
                    kernel_manager=self, parent=self, log=self.log
                )
            self._restarter.start()

    def stop_restarter(self) -> None:
        """Stop the restarter."""
        if self.autorestart and self._restarter is not None:
            self._restarter.stop()

    connect_shell = as_zmqstream(AsyncKernelManager.connect_shell)  # type:ignore[assignment]
    connect_control = as_zmqstream(AsyncKernelManager.connect_control)  # type:ignore[assignment]
    connect_iopub = as_zmqstream(AsyncKernelManager.connect_iopub)  # type:ignore[assignment]
    connect_stdin = as_zmqstream(AsyncKernelManager.connect_stdin)  # type:ignore[assignment]
    connect_hb = as_zmqstream(AsyncKernelManager.connect_hb)  # type:ignore[assignment]
