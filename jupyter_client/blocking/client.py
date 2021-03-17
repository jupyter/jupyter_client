"""Implements a fully blocking kernel client.

Useful for test suites and blocking terminal interfaces.
"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from traitlets import Type  # type: ignore
from jupyter_client.channels import HBChannel, ZMQSocketChannel
from jupyter_client.client import KernelClient, reqrep
from ..util import run_sync


class BlockingKernelClient(KernelClient):
    """A KernelClient with blocking APIs

    ``get_[channel]_msg()`` methods wait for and return messages on channels,
    raising :exc:`queue.Empty` if no message arrives within ``timeout`` seconds.
    """

    #--------------------------------------------------------------------------
    # Channel proxy methods
    #--------------------------------------------------------------------------

    get_shell_msg = run_sync(KernelClient._async_get_shell_msg)
    get_iopub_msg = run_sync(KernelClient._async_get_iopub_msg)
    get_stdin_msg = run_sync(KernelClient._async_get_stdin_msg)
    get_control_msg = run_sync(KernelClient._async_get_control_msg)

    wait_for_ready = run_sync(KernelClient._async_wait_for_ready)

    # The classes to use for the various channels
    shell_channel_class = Type(ZMQSocketChannel)
    iopub_channel_class = Type(ZMQSocketChannel)
    stdin_channel_class = Type(ZMQSocketChannel)
    hb_channel_class = Type(HBChannel)
    control_channel_class = Type(ZMQSocketChannel)


    _recv_reply = run_sync(KernelClient._async_recv_reply)


    # replies come on the shell channel
    execute = run_sync(reqrep(KernelClient._async_execute))
    history = run_sync(reqrep(KernelClient._async_history))
    complete = run_sync(reqrep(KernelClient._async_complete))
    inspect = run_sync(reqrep(KernelClient._async_inspect))
    kernel_info = run_sync(reqrep(KernelClient._async_kernel_info))
    comm_info = run_sync(reqrep(KernelClient._async_comm_info))

    is_alive = run_sync(KernelClient._async_is_alive)
    execute_interactive = run_sync(KernelClient._async_execute_interactive)

    # replies come on the control channel
    shutdown = run_sync(reqrep(KernelClient._async_shutdown, channel='control'))
