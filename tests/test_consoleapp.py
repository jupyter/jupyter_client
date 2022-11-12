"""Tests for the JupyterConsoleApp"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import os
import subprocess

import pytest
from jupyter_core.application import JupyterApp

from jupyter_client.consoleapp import JupyterConsoleApp
from jupyter_client.manager import start_new_kernel


@pytest.fixture
def sshkey(tmp_path):
    os.chdir(tmp_path)
    name = "test_consoleapp"
    subprocess.run(["ssh-keygen", "-f", name, "-N", ""])
    yield name


class MockConsoleApp(JupyterConsoleApp, JupyterApp):
    pass


def test_console_app_no_existing():
    app = MockConsoleApp()
    app.initialize([])


def test_console_app_existing(tmp_path):
    km, kc = start_new_kernel()
    cf = kc.connection_file
    app = MockConsoleApp(connection_file=cf, existing=cf)
    app.initialize([])
    kc.stop_channels()
    km.shutdown_kernel()


def test_console_app_ssh(sshkey, tmp_path):
    km, kc = start_new_kernel()
    cf = kc.connection_file
    os.chdir(tmp_path)
    app = MockConsoleApp(connection_file=cf, existing=cf, sshkey=sshkey)
    app.initialize([])
    kc.stop_channels()
    km.shutdown_kernel()
