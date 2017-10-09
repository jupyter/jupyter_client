import sys

from jupyter_client import KernelManager
from jupyter_client import discovery

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

    def make_manager(self, name):
        return KernelManager(kernel_cmd=['dummy_kernel'])

def test_meta_kernel_finder():
    kf = discovery.KernelFinder(providers=[DummyKernelProvider()])
    assert list(kf.find_kernels()) == \
        [('dummy/sample', {'argv': ['dummy_kernel']})]

    manager = kf.make_manager('dummy/sample')
    assert manager.kernel_cmd == ['dummy_kernel']
