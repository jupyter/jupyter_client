import sys

from jupyter_client import discovery
from jupyter_client.manager2 import KernelManager2ABC

def test_ipykernel_provider():
    import ipykernel  # Fail clearly if ipykernel not installed
    ikf = discovery.IPykernelProvider()

    res = list(ikf.find_kernels())
    assert len(res) == 1, res
    id, info = res[0]
    assert id == 'kernel'
    assert info['argv'][0] == sys.executable

class DummyKernelProvider(discovery.KernelProviderBase):
    """A dummy kernel provider for testing KernelFinder"""
    id = 'dummy'

    def find_kernels(self):
        yield 'sample', {'argv': ['dummy_kernel']}

    def launch(self, name, cwd=None):
        return DummyKernelManager()

class DummyKernelManager(KernelManager2ABC):
    _alive = True
    def is_alive(self):
        """Check whether the kernel is currently alive (e.g. the process exists)
        """
        return self._alive

    def wait(self, timeout):
        """Wait for the kernel process to exit.
        """
        return False

    def signal(self, signum):
        """Send a signal to the kernel."""
        pass

    def interrupt(self):
        pass

    def kill(self):
        self._alive = False

    def get_connection_info(self):
        """Return a dictionary of connection information"""
        return {}

    def relaunch(self):
        return True

def test_meta_kernel_finder():
    kf = discovery.KernelFinder(providers=[DummyKernelProvider()])
    assert list(kf.find_kernels()) == \
        [('dummy/sample', {'argv': ['dummy_kernel']})]

    launcher = kf.launch('dummy/sample')
    assert isinstance(launcher, DummyKernelManager)
