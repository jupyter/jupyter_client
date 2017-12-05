"""Tests for KernelManager2"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os

pjoin = os.path.join
import signal
import sys
import time
from unittest import TestCase

from ipykernel.kernelspec import make_ipkernel_cmd
from jupyter_client.manager2 import (
    KernelManager2, run_kernel, start_new_kernel, shutdown
)
from .utils import test_env, skip_win32

TIMEOUT = 30

SIGNAL_KERNEL_CMD = [sys.executable, '-m', 'jupyter_client.tests.signalkernel',
                         '-f', '{connection_file}']

class TestKernelManager(TestCase):
    def setUp(self):
        self.env_patch = test_env()
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()

    def test_get_connect_info(self):
        km = KernelManager2(make_ipkernel_cmd(), os.getcwd())
        try:
            self.assertEqual(set(km.connection_info.keys()), {
                'ip', 'transport',
                'hb_port', 'shell_port', 'stdin_port', 'iopub_port', 'control_port',
                'key', 'signature_scheme',
            })
        finally:
            km.kill()
            km.cleanup()

    @skip_win32
    def test_signal_kernel_subprocesses(self):
        with run_kernel(SIGNAL_KERNEL_CMD, startup_timeout=5) as kc:
            def execute(cmd):
                reply = kc.execute(cmd, reply=True)
                content = reply['content']
                self.assertEqual(content['status'], 'ok')
                return content

            N = 5
            for i in range(N):
                execute("start")
            time.sleep(1)  # make sure subprocs stay up
            reply = execute('check')
            self.assertEqual(reply['user_expressions']['poll'], [None] * N)

            # start a job on the kernel to be interrupted
            kc.execute('sleep')
            time.sleep(1)  # ensure sleep message has been handled before we interrupt
            kc.interrupt()
            reply = kc.get_shell_msg(TIMEOUT)
            content = reply['content']
            self.assertEqual(content['status'], 'ok')
            self.assertEqual(content['user_expressions']['interrupted'], True)
            # wait up to 5s for subprocesses to handle signal
            for i in range(50):
                reply = execute('check')
                if reply['user_expressions']['poll'] != [-signal.SIGINT] * N:
                    time.sleep(0.1)
                else:
                    break
            # verify that subprocesses were interrupted
            self.assertEqual(reply['user_expressions']['poll'],
                             [-signal.SIGINT] * N)

    def test_start_new_kernel(self):
        km, kc = start_new_kernel(make_ipkernel_cmd(), startup_timeout=5)
        try:
            self.assertTrue(km.is_alive())
            self.assertTrue(kc.is_alive())
        finally:
            shutdown(kc, km)
