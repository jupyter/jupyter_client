"""Implements a fully blocking kernel client.

Useful for test suites and blocking terminal interfaces.
"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

from functools import partial
from getpass import getpass
try:
    from queue import Empty  # Python 3
except ImportError:
    from Queue import Empty  # Python 2
import sys
import time

import zmq

from traitlets import Type
from jupyter_client.channels import HBChannel
from jupyter_client.client import KernelClient
from .channels import ZMQSocketChannel
from ipython_genutils.py3compat import string_types, iteritems
from ..client import validate_string_dict
try:
    monotonic = time.monotonic
except AttributeError:
    # py2
    monotonic = time.time # close enough

try:
    TimeoutError
except NameError:
    # py2
    TimeoutError = RuntimeError


def reqrep(meth):
    def wrapped(self, *args, **kwargs):
        reply = kwargs.pop('reply', False)
        timeout = kwargs.pop('timeout', None)
        msg_id = meth(self, *args, **kwargs)
        if not reply:
            return msg_id

        return self._recv_reply(msg_id, timeout=timeout)
    
    if not meth.__doc__:
        # python -OO removes docstrings,
        # so don't bother building the wrapped docstring
        return wrapped
    
    basedoc, _ = meth.__doc__.split('Returns\n', 1)
    parts = [basedoc.strip()]
    if 'Parameters' not in basedoc:
        parts.append("""
        Parameters
        ----------
        """)
    parts.append("""
        reply: bool (default: False)
            Whether to wait for and return reply
        timeout: float or None (default: None)
            Timeout to use when waiting for a reply

        Returns
        -------
        msg_id: str
            The msg_id of the request sent, if reply=False (default)
        reply: dict
            The reply message for this request, if reply=True
    """)
    wrapped.__doc__ = '\n'.join(parts)
    return wrapped


from ..channels import HBChannel
import asyncio

class HBChannelAyncio(HBChannel):
    def run(self):
        ioloop = asyncio.new_event_loop()
        asyncio.set_event_loop(ioloop)
        # super(HBChannelAyncio, self).run()
        ioloop.run_until_complete(self.run_async())
        # await self.run_async()

    async def run_async(self):
        """The thread's main activity.  Call start() instead."""
        self._create_socket()
        self._running = True
        self._beating = True

        while self._running:
            if self._pause:
                # just sleep, and skip the rest of the loop
                self._exit.wait(self.time_to_dead)
                continue

            since_last_heartbeat = 0.0
            # no need to catch EFSM here, because the previous event was
            # either a recv or connect, which cannot be followed by EFSM
            await self.socket.send(b'ping')
            request_time = time.time()
            ready = self._poll(request_time)
            if ready:
                self._beating = True
                # the poll above guarantees we have something to recv
                await self.socket.recv()
                # sleep the remainder of the cycle
                remainder = self.time_to_dead - (time.time() - request_time)
                if remainder > 0:
                    self._exit.wait(remainder)
                continue
            else:
                # nothing was received within the time limit, signal heart failure
                self._beating = False
                since_last_heartbeat = time.time() - request_time
                self.call_handlers(since_last_heartbeat)
                # and close/reopen the socket, because the REQ/REP cycle has been broken
                self._create_socket()
                continue

    def _poll(self, start_time):
        """poll for heartbeat replies until we reach self.time_to_dead.

        Ignores interrupts, and returns the result of poll(), which
        will be an empty list if no messages arrived before the timeout,
        or the event tuple if there is a message to receive.
        """

        until_dead = self.time_to_dead - (time.time() - start_time)
        # ensure poll at least once
        until_dead = max(until_dead, 1e-3)
        events = []
        from zmq import ZMQError

        while True:
            try:
                events = self.poller.poll(1000 * until_dead)
            except ZMQError as e:
                if e.errno == errno.EINTR:
                    # ignore interrupts during heartbeat
                    # this may never actually happen
                    until_dead = self.time_to_dead - (time.time() - start_time)
                    until_dead = max(until_dead, 1e-3)
                    pass
                else:
                    raise
            except Exception:
                if self._exiting:
                    break
                else:
                    raise
            else:
                break
        return events

class AsyncioKernelClient(KernelClient):
    """A KernelClient with blocking APIs
    
    ``get_[channel]_msg()`` methods wait for and return messages on channels,
    raising :exc:`queue.Empty` if no message arrives within ``timeout`` seconds.
    """
    def _context_default(self):
        import zmq.asyncio
        return zmq.asyncio.Context.instance()
        # return zmq.Context()
    
    # session = Instance('jupyter_client.session.Session')
    # def _session_default(self):
    #     from jupyter_client.session import Session
    #     return Session(parent=self)
    
    def start_channels_async(self, shell=True, iopub=True, stdin=True, hb=True):
        """Starts the channels for this kernel.

        This will create the channels if they do not exist and then start
        them (their activity runs in a thread). If port numbers of 0 are
        being used (random ports) then you must first call
        :meth:`start_kernel`. If the channels have been stopped and you
        call this, :class:`RuntimeError` will be raised.
        """
        if shell:
            self.shell_channel.start()
        if iopub:
            self.iopub_channel.start()
        if stdin:
            self.stdin_channel.start()
            self.allow_stdin = True
        else:
            self.allow_stdin = False
        if hb:
            self.hb_channel.start()
            
    async def wait_for_ready_async(self, timeout=None):
        """Waits for a response when a client is blocked
        
        - Sets future time for timeout
        - Blocks on shell channel until a message is received
        - Exit if the kernel has died
        - If client times out before receiving a message from the kernel, send RuntimeError
        - Flush the IOPub channel
        """
        if timeout is None:
            abs_timeout = float('inf')
        else:
            abs_timeout = time.time() + timeout

        from ..manager import KernelManager
        if not isinstance(self.parent, KernelManager):
            # This Client was not created by a KernelManager,
            # so wait for kernel to become responsive to heartbeats
            # before checking for kernel_info reply
            while not self.is_alive():
                if time.time() > abs_timeout:
                    raise RuntimeError("Kernel didn't respond to heartbeats in %d seconds and timed out" % timeout)
                time.sleep(0.2)

        # Wait for kernel info reply on shell channel
        while True:
            try:
                msg = await self.shell_channel.get_msg(block=True, timeout=1)
            except Empty:
                pass
            else:
                if msg['msg_type'] == 'kernel_info_reply':
                    self._handle_kernel_info_reply(msg)
                    break

            if not self.is_alive():
                raise RuntimeError('Kernel died before replying to kernel_info', self._hb_channel.is_beating(), self.parent.is_alive())

            # Check if current time is ready check time plus timeout
            if time.time() > abs_timeout:
                raise RuntimeError("Kernel didn't respond in %d seconds" % timeout)

        # Flush IOPub channel
        while True:
            try:
                msg = await self.iopub_channel.get_msg(block=True, timeout=0.2)
            except Empty:
                break

    # The classes to use for the various channels
    shell_channel_class = Type(ZMQSocketChannel)
    iopub_channel_class = Type(ZMQSocketChannel)
    stdin_channel_class = Type(ZMQSocketChannel)
    hb_channel_class = Type(HBChannelAyncio)


    def _recv_reply(self, msg_id, timeout=None):
        """Receive and return the reply for a given request"""
        if timeout is not None:
            deadline = monotonic() + timeout
        while True:
            if timeout is not None:
                timeout = max(0, deadline - monotonic())
            try:
                reply = self.get_shell_msg(timeout=timeout)
            except Empty:
                raise TimeoutError("Timeout waiting for reply")
            if reply['parent_header'].get('msg_id') != msg_id:
                # not my reply, someone may have forgotten to retrieve theirs
                continue
            return reply


    # fork = reqrep(KernelClient.fork)
    execute = reqrep(KernelClient.execute)
    history = reqrep(KernelClient.history)
    complete = reqrep(KernelClient.complete)
    inspect = reqrep(KernelClient.inspect)
    kernel_info = reqrep(KernelClient.kernel_info)
    comm_info = reqrep(KernelClient.comm_info)
    shutdown = reqrep(KernelClient.shutdown)


    def _stdin_hook_default(self, msg):
        """Handle an input request"""
        content = msg['content']
        if content.get('password', False):
            prompt = getpass
        elif sys.version_info < (3,):
            prompt = raw_input
        else:
            prompt = input

        try:
            raw_data = prompt(content["prompt"])
        except EOFError:
            # turn EOFError into EOF character
            raw_data = '\x04'
        except KeyboardInterrupt:
            sys.stdout.write('\n')
            return

        # only send stdin reply if there *was not* another request
        # or execution finished while we were reading.
        if not (self.stdin_channel.msg_ready() or self.shell_channel.msg_ready()):
            self.input(raw_data)

    def _output_hook_default(self, msg):
        """Default hook for redisplaying plain-text output"""
        msg_type = msg['header']['msg_type']
        content = msg['content']
        if msg_type == 'stream':
            stream = getattr(sys, content['name'])
            stream.write(content['text'])
        elif msg_type in ('display_data', 'execute_result'):
            sys.stdout.write(content['data'].get('text/plain', ''))
        elif msg_type == 'error':
            print('\n'.join(content['traceback']), file=sys.stderr)

    def _output_hook_kernel(self, session, socket, parent_header, msg):
        """Output hook when running inside an IPython kernel

        adds rich output support.
        """
        msg_type = msg['header']['msg_type']
        if msg_type in ('display_data', 'execute_result', 'error'):
            session.send(socket, msg_type, msg['content'], parent=parent_header)
        else:
            self._output_hook_default(msg)

    def execute_interactive(self, code, silent=False, store_history=True,
                 user_expressions=None, allow_stdin=None, stop_on_error=True,
                 timeout=None, output_hook=None, stdin_hook=None,
                ):
        """Execute code in the kernel interactively

        Output will be redisplayed, and stdin prompts will be relayed as well.
        If an IPython kernel is detected, rich output will be displayed.

        You can pass a custom output_hook callable that will be called
        with every IOPub message that is produced instead of the default redisplay.

        .. versionadded:: 5.0

        Parameters
        ----------
        code : str
            A string of code in the kernel's language.

        silent : bool, optional (default False)
            If set, the kernel will execute the code as quietly possible, and
            will force store_history to be False.

        store_history : bool, optional (default True)
            If set, the kernel will store command history.  This is forced
            to be False if silent is True.

        user_expressions : dict, optional
            A dict mapping names to expressions to be evaluated in the user's
            dict. The expression values are returned as strings formatted using
            :func:`repr`.

        allow_stdin : bool, optional (default self.allow_stdin)
            Flag for whether the kernel can send stdin requests to frontends.

            Some frontends (e.g. the Notebook) do not support stdin requests.
            If raw_input is called from code executed from such a frontend, a
            StdinNotImplementedError will be raised.

        stop_on_error: bool, optional (default True)
            Flag whether to abort the execution queue, if an exception is encountered.

        timeout: float or None (default: None)
            Timeout to use when waiting for a reply

        output_hook: callable(msg)
            Function to be called with output messages.
            If not specified, output will be redisplayed.

        stdin_hook: callable(msg)
            Function to be called with stdin_request messages.
            If not specified, input/getpass will be called.

        Returns
        -------
        reply: dict
            The reply message for this request
        """
        if not self.iopub_channel.is_alive():
            raise RuntimeError("IOPub channel must be running to receive output")
        if allow_stdin is None:
            allow_stdin = self.allow_stdin
        if allow_stdin and not self.stdin_channel.is_alive():
            raise RuntimeError("stdin channel must be running to allow input")
        msg_id = self.execute(code,
                              silent=silent,
                              store_history=store_history,
                              user_expressions=user_expressions,
                              allow_stdin=allow_stdin,
                              stop_on_error=stop_on_error,
        )
        if stdin_hook is None:
            stdin_hook = self._stdin_hook_default
        if output_hook is None:
            # detect IPython kernel
            if 'IPython' in sys.modules:
                from IPython import get_ipython
                ip = get_ipython()
                in_kernel = getattr(ip, 'kernel', False)
                if in_kernel:
                    output_hook = partial(
                        self._output_hook_kernel,
                        ip.display_pub.session,
                        ip.display_pub.pub_socket,
                        ip.display_pub.parent_header,
                    )
        if output_hook is None:
            # default: redisplay plain-text outputs
            output_hook = self._output_hook_default

        # set deadline based on timeout
        if timeout is not None:
            deadline = monotonic() + timeout
        else:
            timeout_ms = None

        poller = zmq.Poller()
        iopub_socket = self.iopub_channel.socket
        poller.register(iopub_socket, zmq.POLLIN)
        if allow_stdin:
            stdin_socket = self.stdin_channel.socket
            poller.register(stdin_socket, zmq.POLLIN)
        else:
            stdin_socket = None

        # wait for output and redisplay it
        while True:
            if timeout is not None:
                timeout = max(0, deadline - monotonic())
                timeout_ms = 1e3 * timeout
            events = dict(poller.poll(timeout_ms))
            if not events:
                raise TimeoutError("Timeout waiting for output")
            if stdin_socket in events:
                req = self.stdin_channel.get_msg(timeout=0)
                stdin_hook(req)
                continue
            if iopub_socket not in events:
                continue

            msg = self.iopub_channel.get_msg(timeout=0)

            if msg['parent_header'].get('msg_id') != msg_id:
                # not from my request
                continue
            output_hook(msg)

            # stop on idle
            if msg['header']['msg_type'] == 'status' and \
            msg['content']['execution_state'] == 'idle':
                break

        # output is done, get the reply
        if timeout is not None:
            timeout = max(0, deadline - monotonic())
        return self._recv_reply(msg_id, timeout=timeout)

    async def execute_async(self, code, silent=False, store_history=True,
                user_expressions=None, allow_stdin=None, stop_on_error=True):
        """Execute code in the kernel.

        Parameters
        ----------
        code : str
            A string of code in the kernel's language.

        silent : bool, optional (default False)
            If set, the kernel will execute the code as quietly possible, and
            will force store_history to be False.

        store_history : bool, optional (default True)
            If set, the kernel will store command history.  This is forced
            to be False if silent is True.

        user_expressions : dict, optional
            A dict mapping names to expressions to be evaluated in the user's
            dict. The expression values are returned as strings formatted using
            :func:`repr`.

        allow_stdin : bool, optional (default self.allow_stdin)
            Flag for whether the kernel can send stdin requests to frontends.

            Some frontends (e.g. the Notebook) do not support stdin requests.
            If raw_input is called from code executed from such a frontend, a
            StdinNotImplementedError will be raised.

        stop_on_error: bool, optional (default True)
            Flag whether to abort the execution queue, if an exception is encountered.

        Returns
        -------
        The msg_id of the message sent.
        """
        if user_expressions is None:
            user_expressions = {}
        if allow_stdin is None:
            allow_stdin = self.allow_stdin


        # Don't waste network traffic if inputs are invalid
        if not isinstance(code, string_types):
            raise ValueError('code %r must be a string' % code)
        validate_string_dict(user_expressions)

        # Create class for content/msg creation. Related to, but possibly
        # not in Session.
        content = dict(code=code, silent=silent, store_history=store_history,
                       user_expressions=user_expressions,
                       allow_stdin=allow_stdin, stop_on_error=stop_on_error
                       )
        msg = self.session.msg('execute_request', content)
        await self.shell_channel.send(msg)
        return msg['header']['msg_id']

    async def kernel_info(self):
        """Request kernel info

        Returns
        -------
        The msg_id of the message sent
        """
        msg = self.session.msg('kernel_info_request')
        # import pdb; pdb.set_trace()
        await self.shell_channel.send(msg)
        return msg['header']['msg_id']
