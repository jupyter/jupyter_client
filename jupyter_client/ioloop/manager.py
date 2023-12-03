"""A kernel manager with an asyncio IOLoop"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import asyncio
import typing as t
from queue import Queue

import zmq
import zmq.asyncio
from traitlets import Instance, Type

from ..manager import AsyncKernelManager, KernelManager
from ..utils import get_event_loop
from .restarter import AsyncIOLoopKernelRestarter, IOLoopKernelRestarter


class ZMQStream:
    """A class that transforms a ZMQ Socket into a synchronous stream.

    The class supports callbacks for message send and receive, and does
    the actual I/O on the asyncio loop.

    It has a similar interface and function as zmq's ZMQStream, but
    does not rely on the tornado event loop.
    """

    __socket: t.Optional[zmq.sugar.socket.Socket]

    def __init__(self, socket: zmq.sugar.socket.Socket):
        self.__socket = socket
        self.__on_recv = None
        self.__on_send = None
        self.__recv_copy = False
        self.__send_queue = Queue()
        self.__polling = False

    def on_send(self, callback):
        """Register a callback to be run every time you call send."""
        self.__on_send = callback

    def on_recv(self, callback, copy=True):
        """Register a callback to be run every time the socket has something to receive."""
        self.__on_recv = callback
        self.__recv_copy = copy
        self.__start_polling()

    def stop_on_recv(self):
        """Turn off the recv callback."""
        self.__on_recv = None

    def stop_on_send(self):
        """Turn off the send callback."""
        self.__on_send = None

    def send(self, msg, flags=0, copy=True, track=False, **kwargs):
        """Send a message, optionally also register a new callback for sends.
        See zmq.socket.send for details.
        """
        kwargs.update(flags=flags, copy=copy, track=track)
        self.__send_queue.put((msg, kwargs))
        self.__start_polling()

    def recv(self, flags, copy=True, track=False):
        assert self.__socket is not None
        value = self.__socket.recv(flags, copy=copy, track=track)
        if self.__on_recv:
            self.__on_recv(value)
        return value

    def close(self, linger: int | None = None) -> None:
        """Close the channel."""
        socket = self.__socket
        if socket is None:
            return
        try:
            socket.close(linger=linger)
        finally:
            self.__socket = None

    def __poll(self):
        if self.__socket is None:
            self.__polling = False
            return
        mask = zmq.POLLIN
        if not self.__send_queue.empty():
            mask |= zmq.POLLOUT
        poll_result = self.__socket.poll(0.1, mask)
        if poll_result == zmq.POLLIN:
            self.recv(zmq.NOBLOCK, copy=self.__recv_copy)
        elif poll_result == zmq.POLLOUT:
            self.__handle_send()
        if self._polling:
            loop = get_event_loop()
            loop.call_soon_threadsafe(self.__poll)

    def __handle_send(self):
        msg, kwargs = self.__send_queue.get_nowait()
        assert self.__socket is not None
        self.__socket.send_multipart(msg, **kwargs)
        if self.__on_send:
            self.__on_send()

    def __start_polling(self):
        if self.__socket and not self.__polling:
            loop = get_event_loop()
            self.__polling = True
            loop.call_soon_threadsafe(self.__poll)

    def __getattr__(self, attr):
        """Pass through to the underlying socket for other methods."""
        if attr.startswith("__"):
            return super().__getattr__(attr)
        if self.__socket is not None:
            return self.__socket.get(attr)


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
        return get_event_loop()

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

    connect_shell = as_zmqstream(KernelManager.connect_shell)
    connect_control = as_zmqstream(KernelManager.connect_control)
    connect_iopub = as_zmqstream(KernelManager.connect_iopub)
    connect_stdin = as_zmqstream(KernelManager.connect_stdin)
    connect_hb = as_zmqstream(KernelManager.connect_hb)


class AsyncIOLoopKernelManager(AsyncKernelManager):
    """An async ioloop kernel manager."""

    loop = Instance(asyncio.AbstractEventLoop)  # type:ignore[type-abstract]

    def _loop_default(self) -> asyncio.AbstractEventLoop:
        return get_event_loop()

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

    connect_shell = as_zmqstream(KernelManager.connect_shell)
    connect_control = as_zmqstream(KernelManager.connect_control)
    connect_iopub = as_zmqstream(KernelManager.connect_iopub)
    connect_stdin = as_zmqstream(KernelManager.connect_stdin)
    connect_hb = as_zmqstream(KernelManager.connect_hb)
