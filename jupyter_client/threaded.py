""" Defines a KernelClient that provides thread-safe sockets with async callbacks on message
replies.
"""
from __future__ import annotations

import asyncio
import atexit
from concurrent.futures import Future
from threading import Thread
from typing import Any, Dict, List, Optional

import zmq
from traitlets import Instance, Type
from traitlets.log import get_logger

from .channels import HBChannel
from .client import KernelClient
from .session import Session
from .utils import ensure_event_loop

# Local imports
# import ZMQError in top-level namespace, to avoid ugly attribute-error messages
# during garbage collection of threads at exit


class ThreadedZMQSocketChannel:
    """A ZMQ socket invoking a callback in the ioloop"""

    session = None
    socket = None
    stream = None
    _inspect = None
    _close_future: Future | None = None
    _stopping = False

    def __init__(
        self,
        socket: Optional[zmq.Socket],
        session: Optional[Session],
        loop: Optional[asyncio.AbstractEventLoop],
    ) -> None:
        """Create a channel.

        Parameters
        ----------
        socket : :class:`zmq.Socket`
            The ZMQ socket to use.
        session : :class:`session.Session`
            The session to use.
        loop
            A ioloop to poll the socket.
        """
        super().__init__()

        self.socket = socket
        self.session = session
        self.ioloop = loop or ensure_event_loop()

    _is_alive = False

    def is_alive(self) -> bool:
        """Whether the channel is alive."""
        return self._is_alive

    def start(self) -> None:
        """Start the channel."""
        if not self._is_alive:
            self.ioloop.call_soon_threadsafe(self._thread_poll)
        self._is_alive = True

    def stop(self) -> None:
        """Stop the channel."""
        self._is_alive = False

    def close(self) -> None:
        """Close the channel."""
        if self.socket is not None:
            f: Future
            self._close_future = f = Future()
            self.ioloop.call_soon_threadsafe(self._thread_close)
            # wait for result
            try:
                f.result(timeout=5)
            except Exception as e:
                log = get_logger()
                msg = f"Error closing socket {self.socket}: {e}"
                log.warning(msg, RuntimeWarning, stacklevel=2)

    def flush(self):
        """Flush the channel."""
        pass

    def _thread_close(self) -> None:
        if self.socket is None:
            return
        try:
            self.socket.close(linger=0)
            self.socket = None
            self._is_alive = False
            if self._close_future is not None:
                self._close_future.set_result(None)
        except Exception as e:
            if self._close_future is not None:
                self._close_future.set_exception(e)

    def _thread_poll(self) -> None:
        if self.socket is None:
            return
        if self.socket.poll(0.1, zmq.POLLIN) == zmq.POLLIN:
            self._handle_recv(self.socket.recv_multipart())
        if self._is_alive:
            self.ioloop.call_soon_threadsafe(self._thread_poll)
            return
        self._thread_close()

    def _thread_send(self, msg: Dict[str, Any]) -> None:
        assert self.session is not None
        if self.socket:
            self.session.send(self.socket, msg)

    def send(self, msg: Dict[str, Any]) -> None:
        """Queue a message to be sent from the IOLoop's thread.

        Parameters
        ----------
        msg : message to send

        This is threadsafe, as it uses IOLoop.add_callback to give the loop's
        thread control of the action.
        """
        assert self.ioloop is not None
        self.ioloop.call_soon_threadsafe(self._thread_send, msg)

    def _handle_recv(self, msg_list: List) -> None:
        """Callback for stream.on_recv.

        Unpacks message, and calls handlers with it.
        """
        assert self.ioloop is not None
        assert self.session is not None
        _, smsg = self.session.feed_identities(msg_list)
        msg = self.session.deserialize(smsg)
        # let client inspect messages
        if self._inspect:
            self._inspect(msg)  # type:ignore[unreachable]
        self.call_handlers(msg)

    def call_handlers(self, msg: Dict[str, Any]) -> None:
        """This method is called in the ioloop thread when a message arrives.

        Subclasses should override this method to handle incoming messages.
        It is important to remember that this method is called in the thread
        so that some logic must be done to ensure that the application level
        handlers are called in the application thread.
        """
        pass

    def process_events(self) -> None:
        """Subclasses should override this with a method
        processing any pending GUI events.
        """
        pass


class IOLoopThread(Thread):
    """Run an asyncio ioloop in a thread to send and receive messages"""

    _exiting = False
    ioloop = None

    def __init__(self) -> None:
        """Initialize an io loop thread."""
        super().__init__()
        self.daemon = True

    @staticmethod
    @atexit.register
    def _notice_exit() -> None:
        # Class definitions can be torn down during interpreter shutdown.
        # We only need to set _exiting flag if this hasn't happened.
        if IOLoopThread is not None:
            IOLoopThread._exiting = True

    def start(self) -> None:
        """Start the IOLoop thread

        Don't return until self.ioloop is defined,
        which is created in the thread
        """
        self._start_future: Future = Future()
        Thread.start(self)
        # wait for start, re-raise any errors
        self._start_future.result(timeout=10)

    def run(self) -> None:
        """Run my loop, ignoring EINTR events in the poller"""
        try:
            self.ioloop = loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        except Exception as e:
            self._start_future.set_exception(e)
        else:
            self._start_future.set_result(None)
        if self.ioloop is not None:
            self.ioloop.run_until_complete(self._async_run())

    async def _async_run(self) -> None:
        """Run forever (until self._exiting is set)"""
        while not self._exiting:
            await asyncio.sleep(1)

    def stop(self) -> None:
        """Stop the channel's event loop and join its thread.

        This calls :meth:`~threading.Thread.join` and returns when the thread
        terminates. :class:`RuntimeError` will be raised if
        :meth:`~threading.Thread.start` is called again.
        """
        self._exiting = True
        self.join()
        self.close()
        self.ioloop = None

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        """Close the io loop thread."""
        if self.ioloop is not None:
            try:
                self.ioloop.close()
            except Exception as e:
                log = get_logger()
                msg = f"Error closing loop {self.ioloop}: {e}"
                log.warning(msg, RuntimeWarning, stacklevel=2)


class ThreadedKernelClient(KernelClient):
    """A KernelClient that provides thread-safe sockets with async callbacks on message replies."""

    @property
    def ioloop(self) -> Optional[asyncio.AbstractEventLoop]:  # type:ignore[override]
        if self.ioloop_thread:
            return self.ioloop_thread.ioloop
        return None

    ioloop_thread = Instance(IOLoopThread, allow_none=True)

    def start_channels(
        self,
        shell: bool = True,
        iopub: bool = True,
        stdin: bool = True,
        hb: bool = True,
        control: bool = True,
    ) -> None:
        """Start the channels on the client."""
        self.ioloop_thread = IOLoopThread()
        self.ioloop_thread.start()

        if shell:
            self.shell_channel._inspect = self._check_kernel_info_reply

        super().start_channels(shell, iopub, stdin, hb, control)

    def _check_kernel_info_reply(self, msg: Dict[str, Any]) -> None:
        """This is run in the ioloop thread when the kernel info reply is received"""
        if msg["msg_type"] == "kernel_info_reply":
            self._handle_kernel_info_reply(msg)
            self.shell_channel._inspect = None

    def stop_channels(self) -> None:
        """Stop the channels on the client."""
        super().stop_channels()
        if self.ioloop_thread and self.ioloop_thread.is_alive():
            self.ioloop_thread.stop()

    iopub_channel_class = Type(ThreadedZMQSocketChannel)  # type:ignore[arg-type]
    shell_channel_class = Type(ThreadedZMQSocketChannel)  # type:ignore[arg-type]
    stdin_channel_class = Type(ThreadedZMQSocketChannel)  # type:ignore[arg-type]
    hb_channel_class = Type(HBChannel)  # type:ignore[arg-type]
    control_channel_class = Type(ThreadedZMQSocketChannel)  # type:ignore[arg-type]

    def is_alive(self) -> bool:
        """Is the kernel process still running?"""
        if self._hb_channel is not None:
            # We don't have access to the KernelManager,
            # so we use the heartbeat.
            return self._hb_channel.is_beating()
        # no heartbeat and not local, we can't tell if it's running,
        # so naively return True
        return True
