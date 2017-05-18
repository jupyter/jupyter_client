from .kernelspec import KernelSpecManager
from .manager import KernelManager


class KernelSpecFinder(object):
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
        return KernelManager(kernel_cmd=spec.argv)  # TODO: env


class IPykernelFinder(object):
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

    def make_manager(self):
        info = self._check_for_kernel()
        if info is None:
            raise Exception("ipykernel is not importable")
        return KernelManager(kernel_cmd=info['spec']['argv'])


class MetaKernelFinder(object):
    def __init__(self):
        self.finders = [
            KernelSpecFinder(),
            IPykernelFinder(),
        ]

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
