
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import errno
import os.path
import sys
import json

from traitlets.config.application import Application
from jupyter_core.application import (
    JupyterApp, base_flags, base_aliases
)
from traitlets import Instance, Dict, Unicode, Bool

from . import __version__
from .kernelspec import KernelSpecManager

class ListKernelSpecs(JupyterApp):
    version = __version__
    description = """List installed kernel specifications."""
    kernel_spec_manager = Instance(KernelSpecManager)
    json_output = Bool(False, help='output spec name and location as machine-readable json.',
            config=True)
    
    flags = {'json': ({'ListKernelSpecs': {'json_output': True}},
                "output spec name and location as machine-readable json."),
             'debug': base_flags['debug'],
            }

    def _kernel_spec_manager_default(self):
        return KernelSpecManager(parent=self, data_dir=self.data_dir)

    def start(self):
        paths = self.kernel_spec_manager.find_kernel_specs()
        specs = {kname: {
                "resources_dir": paths[kname],
                "spec": self.kernel_spec_manager.get_kernel_spec(kname).to_dict() 
            } for kname in paths}
        if not self.json_output:
            if not specs:
                print("No kernels available")
                return
            # pad to width of longest kernel name
            name_len = len(sorted(paths, key=lambda name: len(name))[-1])

            def path_key(item):
                """sort key function for Jupyter path priority"""
                path = item[1]
                for idx, prefix in enumerate(self.jupyter_path):
                    if path.startswith(prefix):
                        return (idx, path)
                # not in jupyter path, artificially added to the front
                return (-1, path)

            print("Available kernels:")
            for kernelname, path in sorted(paths.items(), key=path_key):
                print("  %s    %s" % (kernelname.ljust(name_len), path))
        else:
            print(json.dumps({
                'kernelspecs': specs
            }, indent=2))



class InstallKernelSpec(JupyterApp):
    version = __version__
    description = """Install a kernel specification directory.
    
    Given a SOURCE DIRECTORY containing a kernel spec,
    jupyter will copy that directory into one of the Jupyter kernel directories.
    The default is to install kernelspecs for all users.
    `--user` can be specified to install a kernel only for the current user.
    """
    examples = """
    jupyter kernelspec install /path/to/my_kernel --user
    """
    usage = "jupyter kernelspec install SOURCE_DIR [--options]"
    kernel_spec_manager = Instance(KernelSpecManager)

    def _kernel_spec_manager_default(self):
        return KernelSpecManager(data_dir=self.data_dir)

    sourcedir = Unicode()
    kernel_name = Unicode("", config=True,
        help="Install the kernel spec with this name"
    )
    def _kernel_name_default(self):
        return os.path.basename(self.sourcedir)

    user = Bool(False, config=True,
        help="""
        Try to install the kernel spec to the per-user directory instead of
        the system or environment directory.
        """
    )
    prefix = Unicode('', config=True,
        help="""Specify a prefix to install to, e.g. an env.
        The kernelspec will be installed in PREFIX/share/jupyter/kernels/
        """
    )
    replace = Bool(False, config=True,
        help="Replace any existing kernel spec with this name."
    )

    aliases = {
        'name': 'InstallKernelSpec.kernel_name',
        'prefix': 'InstallKernelSpec.prefix',
    }
    aliases.update(base_aliases)

    flags = {'user': ({'InstallKernelSpec': {'user': True}},
                "Install to the per-user kernel registry"),
             'replace': ({'InstallKernelSpec': {'replace': True}},
                "Replace any existing kernel spec with this name."),
             'debug': base_flags['debug'],
            }

    def parse_command_line(self, argv):
        super(InstallKernelSpec, self).parse_command_line(argv)
        # accept positional arg as profile name
        if self.extra_args:
            self.sourcedir = self.extra_args[0]
        else:
            print("No source directory specified.")
            self.exit(1)

    def start(self):
        if self.user and self.prefix:
            self.exit("Can't specify both user and prefix. Please choose one or the other.")
        try:
            self.kernel_spec_manager.install_kernel_spec(self.sourcedir,
                                                 kernel_name=self.kernel_name,
                                                 user=self.user,
                                                 prefix=self.prefix,
                                                 replace=self.replace,
                                                )
        except OSError as e:
            if e.errno == errno.EACCES:
                print(e, file=sys.stderr)
                if not self.user:
                    print("Perhaps you want to install with `sudo` or `--user`?", file=sys.stderr)
                self.exit(1)
            elif e.errno == errno.EEXIST:
                print("A kernel spec is already present at %s" % e.filename, file=sys.stderr)
                self.exit(1)
            raise

class InstallNativeKernelSpec(JupyterApp):
    version = __version__
    description = """[DEPRECATED] Install the IPython kernel spec directory for this Python."""
    kernel_spec_manager = Instance(KernelSpecManager)

    def _kernel_spec_manager_default(self):
        return KernelSpecManager(data_dir=self.data_dir)

    user = Bool(False, config=True,
        help="""
        Try to install the kernel spec to the per-user directory instead of
        the system or environment directory.
        """
    )

    flags = {'user': ({'InstallNativeKernelSpec': {'user': True}},
                "Install to the per-user kernel registry"),
             'debug': base_flags['debug'],
            }

    def start(self):
        try:
            from ipykernel import kernelspec
        except ImportError:
            print("ipykernel not available, can't install its spec.", file=sys.stderr)
            self.exit(1)
        try:
            kernelspec.install(self.kernel_spec_manager, user=self.user)
        except OSError as e:
            if e.errno == errno.EACCES:
                print(e, file=sys.stderr)
                if not self.user:
                    print("Perhaps you want to install with `sudo` or `--user`?", file=sys.stderr)
                self.exit(1)
            self.exit(e)

class KernelSpecApp(Application):
    version = __version__
    name = "jupyter kernelspec"
    description = """Manage Jupyter kernel specifications."""

    subcommands = Dict({
        'list': (ListKernelSpecs, ListKernelSpecs.description.splitlines()[0]),
        'install': (InstallKernelSpec, InstallKernelSpec.description.splitlines()[0]),
        'install-self': (InstallNativeKernelSpec, InstallNativeKernelSpec.description.splitlines()[0]),
    })

    aliases = {}
    flags = {}

    def start(self):
        if self.subapp is None:
            print("No subcommand specified. Must specify one of: %s"% list(self.subcommands))
            print()
            self.print_description()
            self.print_subcommands()
            self.exit(1)
        else:
            return self.subapp.start()


if __name__ == '__main__':
    KernelSpecApp.launch_instance()
