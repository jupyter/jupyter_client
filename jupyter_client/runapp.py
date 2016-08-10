
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import logging
import signal
import time
import sys

from traitlets.config import catch_config_error
from traitlets import (
    Instance, Dict, Unicode, Bool, List, CUnicode, Any, Float
)
from jupyter_core.application import (
    JupyterApp, base_flags, base_aliases
)

from . import __version__
from .consoleapp import JupyterConsoleApp, app_aliases, app_flags

try:
    import queue
except ImportError:
    import Queue as queue

OUTPUT_TIMEOUT = 10

# copy flags from mixin:
flags = dict(base_flags)
# start with mixin frontend flags:
frontend_flags = dict(app_flags)
# update full dict with frontend flags:
flags.update(frontend_flags)

# copy flags from mixin
aliases = dict(base_aliases)
# start with mixin frontend flags
frontend_aliases = dict(app_aliases)
# load updated frontend flags into full dict
aliases.update(frontend_aliases)

# get flags&aliases into sets, and remove a couple that
# shouldn't be scrubbed from backend flags:
frontend_aliases = set(frontend_aliases.keys())
frontend_flags = set(frontend_flags.keys())

class RunApp(JupyterApp, JupyterConsoleApp):
    version = __version__
    name = "jupyter run"
    description = """Run Jupyter kernel code."""
    flags = Dict(flags)
    aliases = Dict(aliases)
    frontend_aliases = Any(frontend_aliases)
    frontend_flags = Any(frontend_flags)
    kernel_timeout = Float(60, config=True,
        help="""Timeout for giving up on a kernel (in seconds).

        On first connect and restart, the console tests whether the
        kernel is running and responsive by sending kernel_info_requests.
        This sets the timeout in seconds for how long the kernel can take
        before being presumed dead.
        """
    )

    def parse_command_line(self, argv=None):
        super(RunApp, self).parse_command_line(argv)
        self.build_kernel_argv(self.extra_args)
        self.filenames_to_run = self.extra_args[:]

    @catch_config_error
    def initialize(self, argv=None):
        self.log.debug("jupyter run: initialize...")
        super(RunApp, self).initialize(argv)
        JupyterConsoleApp.initialize(self)
        signal.signal(signal.SIGINT, self.handle_sigint)
        self.init_kernel_info()

    def handle_sigint(self, *args):
        if self.kernel_manager:
            self.kernel_manager.interrupt_kernel()
        else:
            print("", file=sys.stderr)
            error("Cannot interrupt kernels we didn't start.\n")

    def init_kernel_info(self):
        """Wait for a kernel to be ready, and store kernel info"""
        timeout = self.kernel_timeout
        tic = time.time()
        self.kernel_client.hb_channel.unpause()
        msg_id = self.kernel_client.kernel_info()
        while True:
            try:
                reply = self.kernel_client.get_shell_msg(timeout=1)
            except queue.Empty:
                if (time.time() - tic) > timeout:
                    raise RuntimeError("Kernel didn't respond to kernel_info_request")
            else:
                if reply['parent_header'].get('msg_id') == msg_id:
                    self.kernel_info = reply['content']
                    return

    def start(self):
        self.log.debug("jupyter run: starting...")
        super(RunApp, self).start()
        for filename in self.filenames_to_run:
            self.log.debug("jupyter run: executing `%s`" % filename)
            with open(filename) as fp:
                cell = fp.read()
            return_code = self.execute_printing_output(cell)
            if return_code:
                raise Exception("jupyter-run error running '%s'" % filename)

    def execute_printing_output(self, cell):
        """
        Run a cell on a KernelClient
        Any output from the cell will be displayed.
        """
        msg_id = self.kernel_client.execute(cell)
        return_code = 0
        while True:
            try:
                msg = self.kernel_client.get_iopub_msg(timeout=OUTPUT_TIMEOUT)
            except queue.Empty:
                raise TimeoutError("Timeout waiting for kernel output")
    
            if msg['parent_header'].get('msg_id') != msg_id:
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
                if msg_type == 'error':
                    print('\n'.join(content['traceback']), file=sys.stderr)
                    return_code = 1
                else:
                    sys.stdout.write(content['data'].get('text/plain', ''))
            else:
                pass
        return return_code

main = launch_new_instance = RunApp.launch_instance

if __name__ == '__main__':
    main()
