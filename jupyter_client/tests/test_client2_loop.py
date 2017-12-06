"""Tests for the ioloop KernelClient running in a separate thread."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.


import os
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

pjoin = os.path.join
from unittest import TestCase

from ipykernel.kernelspec import make_ipkernel_cmd
from jupyter_client.manager2 import KernelManager2, shutdown
from jupyter_client.client2_ioloop import ClientInThread
from .utils import test_env

from ipython_genutils.py3compat import string_types
from IPython.utils.capture import capture_output

TIMEOUT = 30


class TestKernelClient(TestCase):
    def setUp(self):
        self.env_patch = test_env()
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

        # Start a client in a new thread, put received messages in queues.
        self.km = KernelManager2(make_ipkernel_cmd(), cwd='.')
        self.kc = ClientInThread(self.km.get_connection_info(), manager=self.km)
        self.received = {'shell': Queue(), 'iopub': Queue()}
        self.kc.start()
        if not self.kc.started.wait(10.0):
            raise RuntimeError("Failed to start kernel client")
        self.kc.add_handler('shell', self.received['shell'].put)
        self.kc.add_handler('iopub', self.received['iopub'].put)


    def tearDown(self):
        shutdown(self.kc, self.km)
        self.kc.close()
        self.env_patch.stop()

    def _check_reply(self, reply_type, reply):
        self.assertIsInstance(reply, dict)
        self.assertEqual(reply['header']['msg_type'], reply_type + '_reply')
        self.assertEqual(reply['parent_header']['msg_type'],
                         reply_type + '_request')

    def test_history(self):
        kc = self.kc
        msg_id = kc.history(session=0)
        self.assertIsInstance(msg_id, string_types)
        reply = self.received['shell'].get(timeout=TIMEOUT)
        self._check_reply('history', reply)

    def test_inspect(self):
        kc = self.kc
        msg_id = kc.inspect('who cares')
        self.assertIsInstance(msg_id, string_types)
        reply = self.received['shell'].get(timeout=TIMEOUT)
        self._check_reply('inspect', reply)

    def test_complete(self):
        kc = self.kc
        msg_id = kc.complete('who cares')
        self.assertIsInstance(msg_id, string_types)
        reply = self.received['shell'].get(timeout=TIMEOUT)
        self._check_reply('complete', reply)

    def test_kernel_info(self):
        kc = self.kc
        msg_id = kc.kernel_info()
        self.assertIsInstance(msg_id, string_types)
        reply = self.received['shell'].get(timeout=TIMEOUT)
        self._check_reply('kernel_info', reply)

    def test_comm_info(self):
        kc = self.kc
        msg_id = kc.comm_info()
        self.assertIsInstance(msg_id, string_types)
        reply = self.received['shell'].get(timeout=TIMEOUT)
        self._check_reply('comm_info', reply)

    def test_shutdown(self):
        kc = self.kc
        msg_id = kc.shutdown()
        self.assertIsInstance(msg_id, string_types)
        reply = self.received['shell'].get(timeout=TIMEOUT)
        self._check_reply('shutdown', reply)
