from abc import ABCMeta, abstractmethod
import entrypoints
import logging
import six

from .kernelspec import KernelSpecManager
from .manager2 import KernelManager2

log = logging.getLogger(__name__)

class KernelProviderBase(six.with_metaclass(ABCMeta, object)):
    id = None  # Should be a short string identifying the provider class.

    @abstractmethod
    def find_kernels(self):
        """Return an iterator of (kernel_name, kernel_info_dict) tuples."""
        pass

    @abstractmethod
    def launch(self, name, cwd=None):
        """Launch a kernel, return an object with the KernelManager2 interface.

        name will be one of the kernel names produced by find_kernels()

        This method launches and manages the kernel in a blocking manner.
        """
        pass

    def launch_async(self, name, cwd=None):
        """Launch a kernel asynchronously using asyncio.

        name will be one of the kernel names produced by find_kernels()

        This method should act as an asyncio coroutine, returning an object
        with the AsyncKernelManager interface. This closely matches the
        synchronous KernelManager2 interface, but all methods are coroutines.
        """
        raise NotImplementedError()

class KernelSpecProvider(KernelProviderBase):
    """Offers kernel types from installed kernelspec directories.
    """
    id = 'spec'

    def __init__(self):
        self.ksm = KernelSpecManager()

    def find_kernels(self):
        for name, resdir in self.ksm.find_kernel_specs().items():
            spec = self.ksm._get_kernel_spec_by_name(name, resdir)
            yield name, {
                # TODO: get full language info
                'language': {'name': spec.language},
                'display_name': spec.display_name,
                'argv': spec.argv,
            }

    def launch(self, name, cwd=None):
        spec = self.ksm.get_kernel_spec(name)
        return KernelManager2(kernel_cmd=spec.argv, extra_env=spec.env, cwd=cwd)

    def launch_async(self, name, cwd=None):
        from .async_manager import AsyncPopenKernelManager
        spec = self.ksm.get_kernel_spec(name)
        return AsyncPopenKernelManager.launch(
            kernel_cmd=spec.argv, extra_env=spec.env, cwd=cwd)

class IPykernelProvider(KernelProviderBase):
    """Offers a kernel type using the Python interpreter it's running in.

    This checks if ipykernel is importable first.
    """
    id = 'pyimport'

    def _check_for_kernel(self):
        try:
            from ipykernel.kernelspec import RESOURCES, get_kernel_dict
            from ipykernel.ipkernel import IPythonKernel
        except ImportError:
            return None
        else:
            return {
                'spec': get_kernel_dict(),
                'language_info': IPythonKernel.language_info,
                'resources_dir': RESOURCES,
            }

    def find_kernels(self):
        info = self._check_for_kernel()

        if info:
            yield 'kernel', {
                'language': info['language_info'],
                'display_name': info['spec']['display_name'],
                'argv': info['spec']['argv'],
            }

    def launch(self, name, cwd=None):
        info = self._check_for_kernel()
        if info is None:
            raise Exception("ipykernel is not importable")
        return KernelManager2(kernel_cmd=info['spec']['argv'], extra_env={},
                              cwd=cwd)

    def launch_async(self, name, cwd=None):
        from .async_manager import AsyncPopenKernelManager
        info = self._check_for_kernel()
        if info is None:
            raise Exception("ipykernel is not importable")
        return AsyncPopenKernelManager.launch(
            kernel_cmd=info['spec']['argv'], extra_env={}, cwd=cwd)

class KernelFinder(object):
    """Manages a collection of kernel providers to find available kernel types

    *providers* should be a list of kernel provider instances.
    """
    def __init__(self, providers):
        self.providers = providers

    @classmethod
    def from_entrypoints(cls):
        """Load all kernel providers advertised by entry points.

        Kernel providers should use the "jupyter_client.kernel_providers"
        entry point group.

        Returns an instance of KernelFinder.
        """
        providers = []
        for ep in entrypoints.get_group_all('jupyter_client.kernel_providers'):
            try:
                provider = ep.load()()  # Load and instantiate
            except Exception:
                log.error('Error loading kernel provider', exc_info=True)
            else:
                providers.append(provider)

        return cls(providers)

    def find_kernels(self):
        """Iterate over available kernel types.

        Yields 2-tuples of (prefixed_name, attributes)
        """
        for provider in self.providers:
            for kid, attributes in provider.find_kernels():
                id = provider.id + '/' + kid
                yield id, attributes

    def launch(self, name, cwd=None):
        """Launch a kernel of a given kernel type.
        """
        provider_id, kernel_id = name.split('/', 1)
        for provider in self.providers:
            if provider_id == provider.id:
                return provider.launch(kernel_id, cwd)
        raise KeyError(provider_id)

    def launch_async(self, name, cwd=None):
        """Launch a kernel of a given kernel type, using asyncio.
        """
        provider_id, kernel_id = name.split('/', 1)
        for provider in self.providers:
            if provider_id == provider.id:
                return provider.launch_async(kernel_id, cwd)
        raise KeyError(provider_id)
