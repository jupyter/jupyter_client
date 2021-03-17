"""Testing utils for jupyter_client tests

"""
import os
pjoin = os.path.join
import sys
from unittest.mock import patch
from tempfile import TemporaryDirectory
from typing import Dict

import pytest
from jupyter_client import AsyncKernelManager, KernelManager, AsyncMultiKernelManager, MultiKernelManager


skip_win32 = pytest.mark.skipif(sys.platform.startswith('win'), reason="Windows")


class test_env(object):
    """Set Jupyter path variables to a temporary directory
    
    Useful as a context manager or with explicit start/stop
    """
    def start(self):
        self.test_dir = td = TemporaryDirectory()
        self.env_patch = patch.dict(os.environ, {
            'JUPYTER_CONFIG_DIR': pjoin(td.name, 'jupyter'),
            'JUPYTER_DATA_DIR': pjoin(td.name, 'jupyter_data'),
            'JUPYTER_RUNTIME_DIR': pjoin(td.name, 'jupyter_runtime'),
            'IPYTHONDIR': pjoin(td.name, 'ipython'),
            'TEST_VARS': 'test_var_1',
        })
        self.env_patch.start()
    
    def stop(self):
        self.env_patch.stop()
        self.test_dir.cleanup()
    
    def __enter__(self):
        self.start()
        return self.test_dir.name
    
    def __exit__(self, *exc_info):
        self.stop()


def execute(code='', kc=None, **kwargs):
    """wrapper for doing common steps for validating an execution request"""
    from .test_message_spec import validate_message
    if kc is None:
        kc = KC
    msg_id = kc.execute(code=code, **kwargs)
    reply = kc.get_shell_msg(timeout=TIMEOUT)
    validate_message(reply, 'execute_reply', msg_id)
    busy = kc.get_iopub_msg(timeout=TIMEOUT)
    validate_message(busy, 'status', msg_id)
    assert busy['content']['execution_state'] == 'busy'

    if not kwargs.get('silent'):
        execute_input = kc.get_iopub_msg(timeout=TIMEOUT)
        validate_message(execute_input, 'execute_input', msg_id)
        assert execute_input['content']['code'] == code

    return msg_id, reply['content']


def subclass_recorder(f):
    def wrapped(self, *args, **kwargs):
        # record this call
        self.record(f.__name__)
        method = getattr(super(self.__class__, self), f.__name__)
        # call the superclass method
        r = method(*args, **kwargs)
        return r
    return wrapped


class RecordCallMixin:
    method_calls: Dict[str, int]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.method_calls = {}

    def record(self, method_name: str) -> None:
        if method_name not in self.method_calls:
            self.method_calls[method_name] = 0
        self.method_calls[method_name] += 1

    def call_count(self, method_name: str) -> int:
        if method_name not in self.method_calls:
            self.method_calls[method_name] = 0
        return self.method_calls[method_name]

    def reset_counts(self) -> None:
        for record in self.method_calls:
            self.method_calls[record] = 0


class SyncKMSubclass(RecordCallMixin, KernelManager):

    @subclass_recorder
    def start_kernel(self, **kw):
        """ Record call and defer to superclass """

    @subclass_recorder
    def shutdown_kernel(self, now=False, restart=False):
        """ Record call and defer to superclass """

    @subclass_recorder
    def restart_kernel(self, now=False, **kw):
        """ Record call and defer to superclass """

    @subclass_recorder
    def interrupt_kernel(self):
        """ Record call and defer to superclass """

    @subclass_recorder
    def request_shutdown(self, restart=False):
        """ Record call and defer to superclass """

    @subclass_recorder
    def finish_shutdown(self, waittime=None, pollinterval=0.1):
        """ Record call and defer to superclass """

    @subclass_recorder
    def _launch_kernel(self, kernel_cmd, **kw):
        """ Record call and defer to superclass """

    @subclass_recorder
    def _kill_kernel(self):
        """ Record call and defer to superclass """

    @subclass_recorder
    def cleanup_resources(self, restart=False):
        """ Record call and defer to superclass """


class AsyncKMSubclass(RecordCallMixin, AsyncKernelManager):
    """Used to test subclass hierarchies to ensure methods are called when expected.

       This class is also used to test deprecation "routes" that are determined by superclass'
       detection of methods.

       This class represents a current subclass that overrides "interesting" methods of AsyncKernelManager.
    """
    which_cleanup = ""  # cleanup deprecation testing

    @subclass_recorder
    async def start_kernel(self, **kw):
        """ Record call and defer to superclass """

    @subclass_recorder
    async def shutdown_kernel(self, now=False, restart=False):
        """ Record call and defer to superclass """

    @subclass_recorder
    async def restart_kernel(self, now=False, **kw):
        """ Record call and defer to superclass """

    @subclass_recorder
    async def interrupt_kernel(self):
        """ Record call and defer to superclass """

    @subclass_recorder
    def request_shutdown(self, restart=False):
        """ Record call and defer to superclass """

    @subclass_recorder
    async def finish_shutdown(self, waittime=None, pollinterval=0.1):
        """ Record call and defer to superclass """

    @subclass_recorder
    async def _launch_kernel(self, kernel_cmd, **kw):
        """ Record call and defer to superclass """

    @subclass_recorder
    async def _kill_kernel(self):
        """ Record call and defer to superclass """

    def cleanup(self, connection_file=True):
        self.record('cleanup')
        super().cleanup(connection_file=connection_file)
        self.which_cleanup = 'cleanup'

    def cleanup_resources(self, restart=False):
        self.record('cleanup_resources')
        super().cleanup_resources(restart=restart)
        self.which_cleanup = 'cleanup_resources'


class AsyncKernelManagerWithCleanup(AsyncKernelManager):
    """Used to test deprecation "routes" that are determined by superclass' detection of methods.

       This class represents the older subclass that overrides cleanup().  We should find that
       cleanup() is called on these instances via TestAsyncKernelManagerWithCleanup.
    """

    def cleanup(self, connection_file=True):
        super().cleanup(connection_file=connection_file)
        self.which_cleanup = 'cleanup'


class SyncMKMSubclass(RecordCallMixin, MultiKernelManager):

    def _kernel_manager_class_default(self):
        return 'jupyter_client.tests.utils.SyncKMSubclass'

    @subclass_recorder
    def get_kernel(self, kernel_id):
        """ Record call and defer to superclass """

    @subclass_recorder
    def remove_kernel(self, kernel_id):
        """ Record call and defer to superclass """

    @subclass_recorder
    def start_kernel(self, kernel_name=None, **kwargs):
        """ Record call and defer to superclass """

    @subclass_recorder
    def shutdown_kernel(self, kernel_id, now=False, restart=False):
        """ Record call and defer to superclass """

    @subclass_recorder
    def restart_kernel(self, kernel_id, now=False):
        """ Record call and defer to superclass """

    @subclass_recorder
    def interrupt_kernel(self, kernel_id):
        """ Record call and defer to superclass """

    @subclass_recorder
    def request_shutdown(self, kernel_id, restart=False):
        """ Record call and defer to superclass """

    @subclass_recorder
    def finish_shutdown(self, kernel_id, waittime=None, pollinterval=0.1):
        """ Record call and defer to superclass """

    @subclass_recorder
    def cleanup_resources(self, kernel_id, restart=False):
        """ Record call and defer to superclass """

    @subclass_recorder
    def shutdown_all(self, now=False):
        """ Record call and defer to superclass """


class AsyncMKMSubclass(RecordCallMixin, AsyncMultiKernelManager):
    """Used to test subclass hierarchies to ensure methods are called when expected.

       This class is also used to test deprecation "routes" that are determined by superclass'
       detection of methods.

       This class represents a current subclass that overrides "interesting" methods of AsyncKernelManager.
    """
    def _kernel_manager_class_default(self):
        return 'jupyter_client.tests.utils.AsyncKMSubclass'

    @subclass_recorder
    def get_kernel(self, kernel_id):
        """ Record call and defer to superclass """

    @subclass_recorder
    def remove_kernel(self, kernel_id):
        """ Record call and defer to superclass """

    @subclass_recorder
    async def start_kernel(self, kernel_name=None, **kwargs):
        """ Record call and defer to superclass """

    @subclass_recorder
    async def shutdown_kernel(self, kernel_id, now=False, restart=False):
        """ Record call and defer to superclass """

    @subclass_recorder
    async def restart_kernel(self, kernel_id, now=False):
        """ Record call and defer to superclass """

    @subclass_recorder
    async def interrupt_kernel(self, kernel_id):
        """ Record call and defer to superclass """

    @subclass_recorder
    def request_shutdown(self, kernel_id, restart=False):
        """ Record call and defer to superclass """

    @subclass_recorder
    async def finish_shutdown(self, kernel_id, waittime=None, pollinterval=0.1):
        """ Record call and defer to superclass """

    @subclass_recorder
    async def shutdown_all(self, now=False):
        """ Record call and defer to superclass """

    @subclass_recorder
    def cleanup_resources(self, kernel_id, restart=False):
        """ Record call and defer to superclass """
