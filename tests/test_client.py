"""Tests for the KernelClient"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import os
from unittest import TestCase

import pytest
from IPython.utils.capture import capture_output

from .utils import test_env
from jupyter_client.kernelspec import KernelSpecManager
from jupyter_client.kernelspec import NATIVE_KERNEL_NAME
from jupyter_client.kernelspec import NoSuchKernel
from jupyter_client.manager import start_new_async_kernel
from jupyter_client.manager import start_new_kernel

TIMEOUT = 30

pjoin = os.path.join


class TestKernelClient(TestCase):
    def setUp(self):
        self.env_patch = test_env()
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        try:
            KernelSpecManager().get_kernel_spec(NATIVE_KERNEL_NAME)
        except NoSuchKernel:
            pytest.skip()
        self.km, self.kc = start_new_kernel(kernel_name=NATIVE_KERNEL_NAME)

    def tearDown(self):
        self.env_patch.stop()
        self.km.shutdown_kernel()
        self.kc.stop_channels()
        return super().tearDown()

    def test_execute_interactive(self):
        kc = self.kc

        with capture_output() as io:
            reply = kc.execute_interactive("print('hello')", timeout=TIMEOUT)
        assert "hello" in io.stdout
        assert reply["content"]["status"] == "ok"

    def _check_reply(self, reply_type, reply):
        self.assertIsInstance(reply, dict)
        self.assertEqual(reply["header"]["msg_type"], reply_type + "_reply")
        self.assertEqual(reply["parent_header"]["msg_type"], reply_type + "_request")

    def test_history(self):
        kc = self.kc
        msg_id = kc.history(session=0)
        self.assertIsInstance(msg_id, str)
        reply = kc.history(session=0, reply=True, timeout=TIMEOUT)
        self._check_reply("history", reply)

    def test_inspect(self):
        kc = self.kc
        msg_id = kc.inspect("who cares")
        self.assertIsInstance(msg_id, str)
        reply = kc.inspect("code", reply=True, timeout=TIMEOUT)
        self._check_reply("inspect", reply)

    def test_complete(self):
        kc = self.kc
        msg_id = kc.complete("who cares")
        self.assertIsInstance(msg_id, str)
        reply = kc.complete("code", reply=True, timeout=TIMEOUT)
        self._check_reply("complete", reply)

    def test_kernel_info(self):
        kc = self.kc
        msg_id = kc.kernel_info()
        self.assertIsInstance(msg_id, str)
        reply = kc.kernel_info(reply=True, timeout=TIMEOUT)
        self._check_reply("kernel_info", reply)

    def test_comm_info(self):
        kc = self.kc
        msg_id = kc.comm_info()
        self.assertIsInstance(msg_id, str)
        reply = kc.comm_info(reply=True, timeout=TIMEOUT)
        self._check_reply("comm_info", reply)

    def test_shutdown(self):
        kc = self.kc
        reply = kc.shutdown(reply=True, timeout=TIMEOUT)
        self._check_reply("shutdown", reply)

    def test_shutdown_id(self):
        kc = self.kc
        msg_id = kc.shutdown()
        self.assertIsInstance(msg_id, str)


@pytest.fixture
async def kc():
    env_patch = test_env()
    env_patch.start()
    try:
        KernelSpecManager().get_kernel_spec(NATIVE_KERNEL_NAME)
    except NoSuchKernel:
        pytest.skip()
    km, kc = await start_new_async_kernel(kernel_name=NATIVE_KERNEL_NAME)
    yield kc
    env_patch.stop()
    await km.shutdown_kernel()
    kc.stop_channels()


class TestAsyncKernelClient:
    async def test_execute_interactive(self, kc):
        with capture_output() as io:
            reply = await kc.execute_interactive("print('hello')", timeout=TIMEOUT)
        assert "hello" in io.stdout
        assert reply["content"]["status"] == "ok"

    def _check_reply(self, reply_type, reply):
        assert isinstance(reply, dict)
        assert reply["header"]["msg_type"] == reply_type + "_reply"
        assert reply["parent_header"]["msg_type"] == reply_type + "_request"

    async def test_history(self, kc):
        msg_id = await kc.history(session=0)
        assert isinstance(msg_id, str)
        reply = await kc.history(session=0, reply=True, timeout=TIMEOUT)
        self._check_reply("history", reply)

    async def test_inspect(self, kc):
        msg_id = await kc.inspect("who cares")
        assert isinstance(msg_id, str)
        reply = await kc.inspect("code", reply=True, timeout=TIMEOUT)
        self._check_reply("inspect", reply)

    async def test_complete(self, kc):
        msg_id = await kc.complete("who cares")
        assert isinstance(msg_id, str)
        reply = await kc.complete("code", reply=True, timeout=TIMEOUT)
        self._check_reply("complete", reply)

    async def test_kernel_info(self, kc):
        msg_id = await kc.kernel_info()
        assert isinstance(msg_id, str)
        reply = await kc.kernel_info(reply=True, timeout=TIMEOUT)
        self._check_reply("kernel_info", reply)

    async def test_comm_info(self, kc):
        msg_id = await kc.comm_info()
        assert isinstance(msg_id, str)
        reply = await kc.comm_info(reply=True, timeout=TIMEOUT)
        self._check_reply("comm_info", reply)

    async def test_shutdown(self, kc):
        reply = await kc.shutdown(reply=True, timeout=TIMEOUT)
        self._check_reply("shutdown", reply)

    async def test_shutdown_id(self, kc):
        msg_id = await kc.shutdown()
        assert isinstance(msg_id, str)
