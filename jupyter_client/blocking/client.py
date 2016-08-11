"""Implements a fully blocking kernel client.

Useful for test suites and blocking terminal interfaces.
"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

try:
    from queue import Empty  # Python 3
except ImportError:
    from Queue import Empty  # Python 2
import sys
import time

try:
    monotonic = time.monotonic
except AttributeError: # py2
    monotonic = time.clock # close enough

from traitlets import Type
from jupyter_client.channels import HBChannel
from jupyter_client.client import KernelClient
from .channels import ZMQSocketChannel

try:
    TimeoutError
except NameError:
    # py2
    TimeoutError = RuntimeError


class BlockingKernelClient(KernelClient):
    """A BlockingKernelClient """
    
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
                msg = self.shell_channel.get_msg(block=True, timeout=1)
            except Empty:
                pass
            else:
                if msg['msg_type'] == 'kernel_info_reply':
                    self._handle_kernel_info_reply(msg)
                    break

            if not self.is_alive():
                raise RuntimeError('Kernel died before replying to kernel_info')

            # Check if current time is ready check time plus timeout
            if time.time() > abs_timeout:
                raise RuntimeError("Kernel didn't respond in %d seconds" % timeout)

        # Flush IOPub channel
        while True:
            try:
                msg = self.iopub_channel.get_msg(block=True, timeout=0.2)
            except Empty:
                break

    # The classes to use for the various channels
    shell_channel_class = Type(ZMQSocketChannel)
    iopub_channel_class = Type(ZMQSocketChannel)
    stdin_channel_class = Type(ZMQSocketChannel)
    hb_channel_class = Type(HBChannel)

    def run(self, code, silent=False, store_history=True,
                 user_expressions=None, stop_on_error=True,
                 timeout=None,
                ):
        """Run code in the kernel, redisplaying output.

        Wraps a call to `.execute`, capturing and redisplaying any output produced.
        The execute_reply is returned.

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

        stop_on_error: bool, optional (default True)
            Flag whether to abort the execution queue, if an exception is encountered.
        timeout: int or None (default None)
            Timeout (in seconds) to wait for output. If None, wait forever.

        Returns
        -------
        reply: dict
            The execute_reply message.
        """
        if not self.iopub_channel.is_alive():
            raise RuntimeError("IOPub channel must be running to receive output")
        msg_id = self.execute(code,
                              silent=silent,
                              store_history=store_history,
                              user_expressions=user_expressions,
                              stop_on_error=stop_on_error,
        )

        if 'IPython' in sys.modules:
            from IPython import get_ipython
            ip = get_ipython()
            in_kernel = getattr(ip, 'kernel', False)
            if in_kernel:
                socket = ip.display_pub.pub_socket
                session = ip.display_pub.session
                parent_header = ip.display_pub.parent_header
        else:
            in_kernel = False

        # set deadline based on timeout
        start = monotonic()
        if timeout is not None:
            deadline = monotonic() + timeout

        # wait for output and redisplay it
        while True:
            if timeout is not None:
                timeout = max(0, deadline - monotonic())
            try:
                msg = self.get_iopub_msg(timeout=timeout)
            except Empty:
                raise TimeoutError("Timeout waiting for IPython output")

            if msg['parent_header'].get('msg_id') != msg_id:
                # not from my request
                continue
            msg_type = msg['header']['msg_type']
            content = msg['content']
            if msg_type == 'status':
                if content['execution_state'] == 'idle':
                    # idle means output is done
                    break
            elif msg_type == 'stream':
                stream = getattr(sys, content['name'])
                stream.write(content['text'])
            elif msg_type in ('display_data', 'execute_result', 'error'):
                if in_kernel:
                    session.send(socket, msg_type, content, parent=parent_header)
                else:
                    if msg_type == 'error':
                        print('\n'.join(content['traceback']), file=sys.stderr)
                    else:
                        sys.stdout.write(content['data'].get('text/plain', ''))
            else:
                pass

        # output is done, get the reply
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

