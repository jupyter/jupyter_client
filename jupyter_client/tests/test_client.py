"""Tests for the KernelClient"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.


import os
pjoin = os.path.join
from unittest import TestCase

from nose import SkipTest

from jupyter_client.kernelspec import KernelSpecManager, NoSuchKernel, NATIVE_KERNEL_NAME
from ..manager import start_new_kernel
from .utils import test_env

from IPython.utils.capture import capture_output

TIMEOUT = 30

class TestKernelClient(TestCase):
    def setUp(self):
        self.env_patch = test_env()
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()

    def test_run(self):
        try:
            KernelSpecManager().get_kernel_spec(NATIVE_KERNEL_NAME)
        except NoSuchKernel:
            raise SkipTest()
        km, kc = start_new_kernel(kernel_name=NATIVE_KERNEL_NAME)
        self.addCleanup(kc.stop_channels)
        self.addCleanup(km.shutdown_kernel)

        with capture_output() as io:
            reply = kc.run("print('hello')", timeout=TIMEOUT)
        assert 'hello' in io.stdout
        assert reply['content']['status'] == 'ok'
