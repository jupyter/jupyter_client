from .test_discovery import DummyKernelManager, DummyKernelProvider

from jupyter_client import discovery, restarter2

def test_reinstantiate():
    # If the kernel fails before the first poll, a new manager should be
    # instantiated
    kf = discovery.KernelFinder(providers=[DummyKernelProvider()])
    manager = kf.launch('dummy/sample')
    manager.kill()

    restarter = restarter2.KernelRestarterBase(manager, 'dummy/sample',
                                               kernel_finder=kf)
    assert restarter.kernel_manager is manager
    restarter.poll()
    assert restarter.kernel_manager is not manager
    assert restarter.kernel_manager.is_alive()

def test_relaunch():
    # If the kernel fails after the first poll, its manager's relaunch() method
    # should be called.
    kf = discovery.KernelFinder(providers=[DummyKernelProvider()])
    manager = kf.launch('dummy/sample')
    relaunch_count = [0]
    def relaunch():
        relaunch_count[0] += 1
    manager.relaunch = relaunch

    restarter = restarter2.KernelRestarterBase(manager, 'dummy/sample',
                                               kernel_finder=kf)
    restarter.poll()
    assert relaunch_count[0] == 0
    # Kernel dies after first poll
    manager.kill()
    restarter.poll()
    assert relaunch_count[0] == 1
    assert restarter.kernel_manager is manager
