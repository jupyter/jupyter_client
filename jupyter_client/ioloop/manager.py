"""A kernel manager with an asyncio IOLoop"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import asyncio
import typing as t
from queue import Queue

import zmq
import zmq.asyncio
from jupyter_core.utils import ensure_event_loop
from traitlets import Instance, Type

from ..manager import AsyncKernelManager, KernelManager
from .restarter import AsyncIOLoopKernelRestarter, IOLoopKernelRestarter


class ZMQStream:
    """A class that transforms a ZMQ Socket into a synchronous stream.

    The class supports callbacks for message send and receive, and does
    the actual I/O on the asyncio loop.

    It has a similar interface and function as zmq's ZMQStream, but
    does not rely on the tornado event loop.
    """

    socket: t.Optional[zmq.sugar.socket.Socket]

    def __init__(self, socket: zmq.sugar.socket.Socket):
        self.socket = socket
        self.__on_recv: t.Optional[t.Callable] = None
        self.__on_send: t.Optional[t.Callable] = None
        self.__recv_copy = False
        self.__send_queue: Queue[t.Any] = Queue()
        self.__polling = False

    def on_send(self, callback: t.Callable) -> None:
        """Register a callback to be run every time you call send."""
        self.__on_send = callback

    def on_recv(self, callback: t.Callable, copy: bool = True) -> None:
        """Register a callback to be run every time the socket has something to receive."""
        self.__on_recv = callback
        self.__recv_copy = copy
        self.__start_polling()

    def stop_on_recv(self) -> None:
        """Turn off the recv callback."""
        self.__on_recv = None

    def stop_on_send(self) -> None:
        """Turn off the send callback."""
        self.__on_send = None

    def send(
        self, msg: t.Any, flags: int = 0, copy: bool = True, track: bool = False, **kwargs: t.Any
    ) -> None:
        """Send a message, optionally also register a new callback for sends.
        See zmq.socket.send for details.
        """
        kwargs.update(flags=flags, copy=copy, track=track)
        self.__send_queue.put((msg, kwargs))
        self.__start_polling()

    def __recv(self) -> t.Any:
        """Receive data on the channel."""
        assert self.socket is not None
        msg_list = self.socket.recv_multipart(zmq.NOBLOCK, copy=self.__recv_copy)
        if self.__on_recv:
            self.__on_recv(msg_list)
        return msg_list

    def flush(self) -> None:
        """This is a no-op, for backwards compatibility."""

    def close(self, linger: t.Optional[int] = None) -> None:
        """Close the channel."""
        socket = self.socket
        if socket is None:
            return
        try:
            socket.close(linger=linger)
        finally:
            self.socket = None

    def closed(self) -> bool:
        """Check if the channel is closed."""
        if self.socket is None:
            return True
        if self.socket.closed:
            # underlying socket has been closed, but not by us!
            # trigger our cleanup
            self.close()
            return True
        return False

    def __poll(self) -> None:
        if self.socket is None:
            self.__polling = False
            return
        mask = zmq.POLLIN
        if not self.__send_queue.empty():
            mask |= zmq.POLLOUT
        poll_result = self.socket.poll(0.1, mask)
        if poll_result == zmq.POLLIN:
            self.__recv()
        elif poll_result == zmq.POLLOUT:
            self.__handle_send()
        if self.__polling:
            loop = ensure_event_loop()
            loop.call_soon_threadsafe(self.__poll)

    def __handle_send(self) -> None:
        msg, kwargs = self.__send_queue.get_nowait()
        assert self.socket is not None
        self.socket.send_multipart([msg], **kwargs)
        if self.__on_send:
            self.__on_send()

    def __start_polling(self) -> None:
        if self.socket and not self.__polling:
            loop = ensure_event_loop()
            self.__polling = True
            loop.call_soon_threadsafe(self.__poll)

    def __getattr__(self, attr: str) -> t.Any:
        """Pass through to the underlying socket for other methods."""
        if attr.startswith("__"):
            return super().__getattr__(attr)  # type:ignore[misc]
        if self.socket is not None:
            return getattr(self.socket, attr)


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
