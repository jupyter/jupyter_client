"""Implements an async kernel client"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from traitlets import (Type, Instance)  # type: ignore
from jupyter_client.channels import HBChannel, ZMQSocketChannel
from jupyter_client.client import KernelClient, reqrep


def wrapped(meth, channel):
    def _(self, *args, **kwargs):
        reply = kwargs.pop('reply', False)
        timeout = kwargs.pop('timeout', None)
        msg_id = meth(self, *args, **kwargs)
        if not reply:
            return msg_id
        return self._async_recv_reply(msg_id, timeout=timeout, channel=channel)
    return _


class AsyncKernelClient(KernelClient):
    """A KernelClient with async APIs

    ``get_[channel]_msg()`` methods wait for and return messages on channels,
    raising :exc:`queue.Empty` if no message arrives within ``timeout`` seconds.
    """

    #--------------------------------------------------------------------------
    # Channel proxy methods
    #--------------------------------------------------------------------------

    get_shell_msg = KernelClient._async_get_shell_msg
    get_iopub_msg = KernelClient._async_get_iopub_msg
    get_stdin_msg = KernelClient._async_get_stdin_msg
    get_control_msg = KernelClient._async_get_control_msg

    wait_for_ready = KernelClient._async_wait_for_ready

    # The classes to use for the various channels
    shell_channel_class = Type(ZMQSocketChannel)
    iopub_channel_class = Type(ZMQSocketChannel)
    stdin_channel_class = Type(ZMQSocketChannel)
    hb_channel_class = Type(HBChannel)
    control_channel_class = Type(ZMQSocketChannel)


    _recv_reply = KernelClient._async_recv_reply


    # replies come on the shell channel
    execute = reqrep(wrapped, KernelClient._execute)
    history = reqrep(wrapped, KernelClient._history)
    complete = reqrep(wrapped, KernelClient._complete)
    inspect = reqrep(wrapped, KernelClient._inspect)
    kernel_info = reqrep(wrapped, KernelClient._kernel_info)
    comm_info = reqrep(wrapped, KernelClient._comm_info)

    is_alive = KernelClient._async_is_alive
    execute_interactive = KernelClient._async_execute_interactive

    # replies come on the control channel
    shutdown = reqrep(wrapped, KernelClient._shutdown, channel='control')
