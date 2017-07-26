from abc import ABC, abstractmethod
import entrypoints
import logging

from .kernelspec import KernelSpecManager
from .manager import KernelManager

log = logging.getLogger(__name__)

class KernelFinderBase(ABC):
    id = None  # Should be a short string identifying the finder class.

    @abstractmethod
    def find_kernels(self):
        """Return an iterator of (kernel_name, kernel_info_dict) tuples."""
        pass

    @abstractmethod
    def make_manager(self, name):
        """Make and return a KernelManager instance to start a specified kernel

        name will be one of the kernel names produced by find_kernels()
        """
        pass

class KernelSpecFinder(KernelFinderBase):
    """Find kernels from installed kernelspec directories.
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

    def make_manager(self, name):
        spec = self.ksm.get_kernel_spec(name)
        return KernelManager(kernel_cmd=spec.argv, extra_env=spec.env)


class IPykernelFinder(KernelFinderBase):
    """Find ipykernel on this Python version by trying to import it.
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

    def make_manager(self, name):
        info = self._check_for_kernel()
        if info is None:
            raise Exception("ipykernel is not importable")
        return KernelManager(kernel_cmd=info['spec']['argv'])


class MetaKernelFinder(object):
    def __init__(self, finders):
        self.finders = finders

    @classmethod
    def from_entrypoints(cls):
        finders = []
        for ep in entrypoints.get_group_all('jupyter_client.kernel_finders'):
            try:
                finder = ep.load()()  # Load and instantiate
            except Exception:
                log.error('Error loading kernel finder', exc_info=True)
            else:
                finders.append(finder)

        return cls(finders)

    def find_kernels(self):
        for finder in self.finders:
            for kid, attributes in finder.find_kernels():
                id = finder.id + '/' + kid
                yield id, attributes

    def make_manager(self, id):
        finder_id, kernel_id = id.split('/', 1)
        for finder in self.finders:
            if finder_id == finder.id:
                return finder.make_manager(kernel_id)
