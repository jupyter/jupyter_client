"""Tests for the kernelspecapp"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import os
import warnings

from jupyter_client.kernelspecapp import InstallKernelSpec
from jupyter_client.kernelspecapp import KernelSpecApp
from jupyter_client.kernelspecapp import ListKernelSpecs
from jupyter_client.kernelspecapp import ListProvisioners
from jupyter_client.kernelspecapp import RemoveKernelSpec


def test_kernelspec_sub_apps(kernel_spec):
    app = InstallKernelSpec()
    prefix = os.path.dirname(os.environ['JUPYTER_DATA_DIR'])
    kernel_dir = os.path.join(prefix, 'share/jupyter/kernels')
    app.kernel_spec_manager.kernel_dirs.append(kernel_dir)
    app.prefix = prefix = prefix
    app.initialize([kernel_spec])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        app.start()

    app = ListKernelSpecs()
    app.kernel_spec_manager.kernel_dirs.append(kernel_dir)
    specs = app.start()
    assert 'test' in specs

    app = RemoveKernelSpec(spec_names=['test'], force=True)
    app.kernel_spec_manager.kernel_dirs.append(kernel_dir)
    app.start()

    app = ListKernelSpecs()
    app.kernel_spec_manager.kernel_dirs.append(kernel_dir)
    specs = app.start()
    assert 'test' not in specs


def test_kernelspec_app():
    app = KernelSpecApp()
    app.initialize(["list"])
    app.start()


def test_list_provisioners_app():
    app = ListProvisioners()
    app.initialize([])
    app.start()
