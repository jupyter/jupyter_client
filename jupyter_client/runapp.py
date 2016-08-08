
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import logging
import signal

from traitlets.config.application import Application
from traitlets.config import catch_config_error
from traitlets import (
    Instance, Dict, Unicode, Bool, List, CUnicode, Any
)
from jupyter_core.application import (
    JupyterApp, base_flags, base_aliases
)

from . import __version__
from .consoleapp import JupyterConsoleApp, app_aliases, app_flags

from jupyter_console.ptshell import ZMQTerminalInteractiveShell

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

    def parse_command_line(self, argv=None):
        super(RunApp, self).parse_command_line(argv)
        self.build_kernel_argv(self.extra_args)
        self.filenames_to_run = self.extra_args[:]

    @catch_config_error
    def initialize(self, argv=None):
        super(RunApp, self).initialize(argv)
        JupyterConsoleApp.initialize(self)
        signal.signal(signal.SIGINT, self.handle_sigint)
        self.shell = ZMQTerminalInteractiveShell.instance(parent=self,
                        manager=self.kernel_manager,
                        client=self.kernel_client,
        )
        self.shell.own_kernel = not self.existing

    def handle_sigint(self, *args):
        if self.shell._executing:
            if self.kernel_manager:
                self.kernel_manager.interrupt_kernel()
            else:
                print("", file=sys.stderr)
                error("Cannot interrupt kernels we didn't start.\n")
        else:
            # raise the KeyboardInterrupt if we aren't waiting for execution,
            # so that the interact loop advances, and prompt is redrawn, etc.
            raise KeyboardInterrupt

    def start(self):
        super(RunApp, self).start()
        for filename in self.filenames_to_run:
            cell = open(filename).read()
            self.shell.run_cell(cell, False)

main = launch_new_instance = RunApp.launch_instance

if __name__ == '__main__':
    main()
