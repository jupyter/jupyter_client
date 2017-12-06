"""Base class to manage the interaction with a running kernel"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import absolute_import, print_function

from functools import partial
from getpass import getpass
from six.moves import input
import sys
import time
import zmq

from ipython_genutils.py3compat import string_types, iteritems
from traitlets.log import get_logger as get_app_logger
from .channels import major_protocol_version, HBChannel
from .session import Session
from .util import inherit_docstring

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


channel_socket_types = {
    'hb' : zmq.REQ,
    'shell' : zmq.DEALER,
    'iopub' : zmq.SUB,
    'stdin' : zmq.DEALER,
    'control': zmq.DEALER,
}

# some utilities to validate message structure, these might get moved elsewhere
# if they prove to have more generic utility

def validate_string_dict(dct):
    """Validate that the input is a dict with string keys and values.

    Raises ValueError if not."""
    for k, v in iteritems(dct):
        if not isinstance(k, string_types):
            raise ValueError('key %r in dict must be a string' % k)
        if not isinstance(v, string_types):
            raise ValueError('value %r in dict must be a string' % v)

class KernelClient2(object):
    """Communicates with a single kernel on any host via zmq channels.

    The messages that can be sent are exposed as methods of the
    client (KernelClient2.execute, complete, history, etc.). These methods only
    send the message, they don't wait for a reply. To get results, use e.g.
    :meth:`get_shell_msg` to fetch messages from the shell channel.
    """
    hb_monitor = None

    def __init__(self, connection_info, manager=None, use_heartbeat=True):
        self.connection_info = connection_info
        self.manager = manager
        self.using_heartbeat = use_heartbeat and (manager is not None)
        self.context = zmq.Context.instance()
        self.session = Session(key=connection_info['key'].encode('ascii'),
                           signature_scheme=connection_info['signature_scheme'])
        self.log = get_app_logger()

        identity = self.session.bsession
        self.iopub_socket = self._create_connected_socket('iopub', identity)
        self.iopub_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.shell_socket = self._create_connected_socket('shell', identity)
        self.stdin_socket = self._create_connected_socket('stdin', identity)
        self.control_socket = self._create_connected_socket('control', identity)
        if self.using_heartbeat:
            self.hb_monitor = HBChannel(context=self.context,
                                        address=self._make_url('hb'))
            self.hb_monitor.start()

    @property
    def owned_kernel(self):
        """True if this client 'owns' the kernel, i.e. started it."""
        return self.manager is not None

    def close(self):
        """Close sockets of this client.

        After calling this, the client can no longer be used.
        """
        self.iopub_socket.close()
        self.shell_socket.close()
        self.stdin_socket.close()
        self.control_socket.close()
        if self.hb_monitor:
            self.hb_monitor.stop()

    # flag for whether execute requests should be allowed to call raw_input:
    allow_stdin = True

    def _make_url(self, channel):
        """Make a ZeroMQ URL for a given channel."""
        transport = self.connection_info['transport']
        ip = self.connection_info['ip']
        port = self.connection_info['%s_port' % channel]

        if transport == 'tcp':
            return "tcp://%s:%i" % (ip, port)
        else:
            return "%s://%s-%s" % (transport, ip, port)

    def _create_connected_socket(self, channel, identity=None):
        """Create a zmq Socket and connect it to the kernel."""
        url = self._make_url(channel)
        socket_type = channel_socket_types[channel]
        self.log.debug("Connecting to: %s" % url)
        sock = self.context.socket(socket_type)
        # set linger to 1s to prevent hangs at exit
        sock.linger = 1000
        if identity:
            sock.identity = identity
        sock.connect(url)
        return sock

    def is_alive(self):
        if self.owned_kernel:
            return self.manager.is_alive()
        elif self.using_heartbeat:
            return self.hb_monitor.is_beating()
        else:
            return True  # Fingers crossed

    def _send(self, socket, msg):
        self.session.send(socket, msg)

    # Methods to send specific messages on channels
    def execute(self, code, silent=False, store_history=True,
                user_expressions=None, allow_stdin=None, stop_on_error=True,
                _header=None):
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
        msg = self.session.msg('execute_request', content, header=_header)
        self._send(self.shell_socket, msg)
        return msg['header']['msg_id']

    def complete(self, code, cursor_pos=None, _header=None):
        """Tab complete text in the kernel's namespace.

        Parameters
        ----------
        code : str
            The context in which completion is requested.
            Can be anything between a variable name and an entire cell.
        cursor_pos : int, optional
            The position of the cursor in the block of code where the completion was requested.
            Default: ``len(code)``

        Returns
        -------
        The msg_id of the message sent.
        """
        if cursor_pos is None:
            cursor_pos = len(code)
        content = dict(code=code, cursor_pos=cursor_pos)
        msg = self.session.msg('complete_request', content, header=_header)
        self._send(self.shell_socket, msg)
        return msg['header']['msg_id']

    def inspect(self, code, cursor_pos=None, detail_level=0, _header=None):
        """Get metadata information about an object in the kernel's namespace.

        It is up to the kernel to determine the appropriate object to inspect.

        Parameters
        ----------
        code : str
            The context in which info is requested.
            Can be anything between a variable name and an entire cell.
        cursor_pos : int, optional
            The position of the cursor in the block of code where the info was requested.
            Default: ``len(code)``
        detail_level : int, optional
            The level of detail for the introspection (0-2)

        Returns
        -------
        The msg_id of the message sent.
        """
        if cursor_pos is None:
            cursor_pos = len(code)
        content = dict(code=code, cursor_pos=cursor_pos,
                       detail_level=detail_level,
                       )
        msg = self.session.msg('inspect_request', content, header=_header)
        self._send(self.shell_socket, msg)
        return msg['header']['msg_id']

    def history(self, raw=True, output=False, hist_access_type='range',
                _header=None, **kwargs):
        """Get entries from the kernel's history list.

        Parameters
        ----------
        raw : bool
            If True, return the raw input.
        output : bool
            If True, then return the output as well.
        hist_access_type : str
            'range' (fill in session, start and stop params), 'tail' (fill in n)
             or 'search' (fill in pattern param).

        session : int
            For a range request, the session from which to get lines. Session
            numbers are positive integers; negative ones count back from the
            current session.
        start : int
            The first line number of a history range.
        stop : int
            The final (excluded) line number of a history range.

        n : int
            The number of lines of history to get for a tail request.

        pattern : str
            The glob-syntax pattern for a search request.

        Returns
        -------
        The ID of the message sent.
        """
        if hist_access_type == 'range':
            kwargs.setdefault('session', 0)
            kwargs.setdefault('start', 0)
        content = dict(raw=raw, output=output,
                       hist_access_type=hist_access_type,
                       **kwargs)
        msg = self.session.msg('history_request', content, header=_header)
        self._send(self.shell_socket, msg)
        return msg['header']['msg_id']

    def kernel_info(self, _header=None):
        """Request kernel info

        Returns
        -------
        The msg_id of the message sent
        """
        msg = self.session.msg('kernel_info_request', header=_header)
        self._send(self.shell_socket, msg)
        return msg['header']['msg_id']

    def comm_info(self, target_name=None, _header=None):
        """Request comm info

        Returns
        -------
        The msg_id of the message sent
        """
        if target_name is None:
            content = {}
        else:
            content = dict(target_name=target_name)
        msg = self.session.msg('comm_info_request', content, header=_header)
        self._send(self.shell_socket, msg)
        return msg['header']['msg_id']

    def _handle_kernel_info_reply(self, msg):
        """handle kernel info reply

        sets protocol adaptation version. This might
        be run from a separate thread.
        """
        adapt_version = int(msg['content']['protocol_version'].split('.')[0])
        if adapt_version != major_protocol_version:
            self.session.adapt_version = adapt_version

    def shutdown(self, restart=False, _header=None):
        """Request an immediate kernel shutdown.

        Upon receipt of the (empty) reply, client code can safely assume that
        the kernel has shut down and it's safe to forcefully terminate it if
        it's still alive.

        The kernel will send the reply via a function registered with Python's
        atexit module, ensuring it's truly done as the kernel is done with all
        normal operation.

        Returns
        -------
        The msg_id of the message sent
        """
        # Send quit message to kernel. Once we implement kernel-side setattr,
        # this should probably be done that way, but for now this will do.
        msg = self.session.msg('shutdown_request', {'restart': restart},
                               header=_header)
        self._send(self.shell_socket, msg)
        return msg['header']['msg_id']

    def is_complete(self, code, _header=None):
        """Ask the kernel whether some code is complete and ready to execute."""
        msg = self.session.msg('is_complete_request', {'code': code},
                               header=_header)
        self._send(self.shell_socket, msg)
        return msg['header']['msg_id']

    def interrupt(self, _header=None):
        """Send an interrupt message/signal to the kernel"""
        mode = self.connection_info.get('interrupt_mode', 'signal')
        if mode == 'message':
            msg = self.session.msg("interrupt_request", content={},
                                   header=_header)
            self._send(self.control_socket, msg)
            return msg['header']['msg_id']
        elif self.owned_kernel:
            self.manager.interrupt()
        else:
            self.log.warning("Can't send signal to non-owned kernel")

    def input(self, string, parent=None, _header=None):
        """Send a string of raw input to the kernel.

        This should only be called in response to the kernel sending an
        ``input_request`` message on the stdin channel.
        """
        content = dict(value=string)
        msg = self.session.msg('input_reply', content,
                               header=_header, parent=parent)
        self._send(self.stdin_socket, msg)


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


class BlockingKernelClient2(KernelClient2):
    """A KernelClient with blocking APIs

    ``get_[channel]_msg()`` methods wait for and return messages on channels,
    returning None if no message arrives within ``timeout`` seconds.
    """

    def _recv(self, socket):
        """Receive and parse a message"""
        msg = socket.recv_multipart()
        ident,smsg = self.session.feed_identities(msg)
        return self.session.deserialize(smsg)

    def _get_msg(self, socket, block=True, timeout=None):
        if block:
            if timeout is not None:
                timeout *= 1000  # seconds to ms
            ready = socket.poll(timeout)
        else:
            ready = socket.poll(timeout=0)

        if ready:
            return self._recv(socket)

    def get_shell_msg(self, block=True, timeout=None):
        """Get a message from the shell channel"""
        return self._get_msg(self.shell_socket, block, timeout)

    def get_iopub_msg(self, block=True, timeout=None):
        """Get a message from the iopub channel"""
        return self._get_msg(self.iopub_socket, block, timeout)

    def get_stdin_msg(self, block=True, timeout=None):
        """Get a message from the stdin channel"""
        return self._get_msg(self.stdin_socket, block, timeout)

    def wait_for_ready(self, timeout=None):
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

        if not self.owned_kernel:
            # This Client was not created by a KernelManager,
            # so wait for kernel to become responsive to heartbeats
            # before checking for kernel_info reply
            while not self.is_alive():
                if time.time() > abs_timeout:
                    raise RuntimeError(
                        "Kernel didn't respond to heartbeats in %d seconds and timed out" % timeout)
                time.sleep(0.2)

        self.kernel_info(reply=False)

        # Wait for kernel info reply on shell channel
        while True:
            msg = self.get_shell_msg(timeout=1)
            if msg and msg['msg_type'] == 'kernel_info_reply':
                self._handle_kernel_info_reply(msg)
                break

            if not self.is_alive():
                raise RuntimeError('Kernel died before replying to kernel_info')

            # Check if current time is ready check time plus timeout
            if time.time() > abs_timeout:
                raise RuntimeError(
                    "Kernel didn't respond in %d seconds" % timeout)

        # Flush IOPub channel
        while True:
            msg = self.get_iopub_msg(block=True, timeout=0.2)
            if msg is None:
                break

    def _recv_reply(self, msg_id, timeout=None):
        """Receive and return the reply for a given request"""
        deadline = None
        if timeout is not None:
            deadline = monotonic() + timeout
        while True:
            if timeout is not None:
                timeout = max(0, deadline - monotonic())
            reply = self.get_shell_msg(timeout=timeout)
            if reply is None:
                raise TimeoutError("Timeout waiting for reply")
            elif reply['parent_header'].get('msg_id') != msg_id:
                # not my reply, someone may have forgotten to retrieve theirs
                continue
            return reply

    execute = reqrep(KernelClient2.execute)
    history = reqrep(KernelClient2.history)
    complete = reqrep(KernelClient2.complete)
    inspect = reqrep(KernelClient2.inspect)
    kernel_info = reqrep(KernelClient2.kernel_info)
    comm_info = reqrep(KernelClient2.comm_info)
    shutdown = reqrep(KernelClient2.shutdown)

    @inherit_docstring(KernelClient2)
    def interrupt(self, reply=False, timeout=None):
        msg_id = super(BlockingKernelClient2, self).interrupt()
        if reply and msg_id:
            return self._recv_reply(msg_id, timeout=timeout)
        else:
            return msg_id

    def _stdin_hook_default(self, msg):
        """Handle an input request"""
        content = msg['content']
        if content.get('password', False):
            prompt = getpass
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
        if not (self.stdin_socket.poll(timeout=0)
                or self.shell_socket.poll(timeout=0)):
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
                            user_expressions=None, allow_stdin=None,
                            stop_on_error=True,
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
        if allow_stdin is None:
            allow_stdin = self.allow_stdin
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
        timeout_ms = None
        if timeout is not None:
            deadline = monotonic() + timeout
        else:
            deadline = None

        poller = zmq.Poller()
        poller.register(self.iopub_socket, zmq.POLLIN)
        if allow_stdin:
            poller.register(self.stdin_socket, zmq.POLLIN)

        # wait for output and redisplay it
        while True:
            if deadline is not None:
                timeout = max(0, deadline - monotonic())
                timeout_ms = 1e3 * timeout
            events = dict(poller.poll(timeout_ms))
            if not events:
                raise TimeoutError("Timeout waiting for output")
            if self.stdin_socket in events:
                req = self.get_stdin_msg(timeout=0)
                stdin_hook(req)
                continue
            if self.iopub_socket not in events:
                continue

            msg = self.get_iopub_msg(timeout=0)

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
