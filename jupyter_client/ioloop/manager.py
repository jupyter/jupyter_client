"""A kernel manager with a tornado IOLoop"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import asyncio

import zmq
from tornado import ioloop
from traitlets import Instance
from traitlets import Type
from zmq.eventloop.zmqstream import gen_log
from zmq.eventloop.zmqstream import ZMQStream

from .restarter import AsyncIOLoopKernelRestarter
from .restarter import IOLoopKernelRestarter
from jupyter_client.manager import AsyncKernelManager
from jupyter_client.manager import KernelManager


class _ZMQStream(ZMQStream):
    def _handle_recv(self):
        """Handle a recv event."""
        if self._flushed:
            return
        try:
            msg = self.socket.recv_multipart(zmq.NOBLOCK, copy=self._recv_copy)
            if isinstance(msg, asyncio.Future):
                msg = msg.result()
        except zmq.ZMQError as e:
            if e.errno == zmq.EAGAIN:
                # state changed since poll event
                pass
            else:
                raise
        else:
            if self._recv_callback:
                callback = self._recv_callback
                self._run_callback(callback, msg)

    def _handle_send(self):
        """Handle a send event."""
        if self._flushed:
            return
        if not self.sending():
            gen_log.error("Shouldn't have handled a send event")
            return

        msg, kwargs = self._send_queue.get()
        try:
            status = self.socket.send_multipart(msg, **kwargs)
            if isinstance(status, asyncio.Future):
                status = status.result()
        except zmq.ZMQError as e:
            gen_log.error("SEND Error: %s", e)
            status = e
        if self._send_callback:
            callback = self._send_callback
            self._run_callback(callback, msg, status)


def as_zmqstream(f):
    def wrapped(self, *args, **kwargs):
        socket = f(self, *args, **kwargs)
        return _ZMQStream(socket, self.loop)

    return wrapped


class IOLoopKernelManager(KernelManager):

    loop = Instance("tornado.ioloop.IOLoop")

    def _loop_default(self):
        return ioloop.IOLoop.current()

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
    _restarter = Instance("jupyter_client.ioloop.IOLoopKernelRestarter", allow_none=True)

    def start_restarter(self):
        if self.autorestart and self.has_kernel:
            if self._restarter is None:
                self._restarter = self.restarter_class(
                    kernel_manager=self, loop=self.loop, parent=self, log=self.log
                )
            self._restarter.start()

    def stop_restarter(self):
        if self.autorestart:
            if self._restarter is not None:
                self._restarter.stop()

    connect_shell = as_zmqstream(KernelManager.connect_shell)
    connect_control = as_zmqstream(KernelManager.connect_control)
    connect_iopub = as_zmqstream(KernelManager.connect_iopub)
    connect_stdin = as_zmqstream(KernelManager.connect_stdin)
    connect_hb = as_zmqstream(KernelManager.connect_hb)


class AsyncIOLoopKernelManager(AsyncKernelManager):

    loop = Instance("tornado.ioloop.IOLoop")

    def _loop_default(self):
        return ioloop.IOLoop.current()

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
    _restarter = Instance("jupyter_client.ioloop.AsyncIOLoopKernelRestarter", allow_none=True)

    def start_restarter(self):
        if self.autorestart and self.has_kernel:
            if self._restarter is None:
                self._restarter = self.restarter_class(
                    kernel_manager=self, loop=self.loop, parent=self, log=self.log
                )
            self._restarter.start()

    def stop_restarter(self):
        if self.autorestart:
            if self._restarter is not None:
                self._restarter.stop()

    connect_shell = as_zmqstream(AsyncKernelManager.connect_shell)
    connect_control = as_zmqstream(AsyncKernelManager.connect_control)
    connect_iopub = as_zmqstream(AsyncKernelManager.connect_iopub)
    connect_stdin = as_zmqstream(AsyncKernelManager.connect_stdin)
    connect_hb = as_zmqstream(AsyncKernelManager.connect_hb)
