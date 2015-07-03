import io
import json
from logging import StreamHandler
import os
from os.path import join as pjoin
import unittest

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

if str is bytes: # py2
    StringIO = io.BytesIO
else:
    StringIO = io.StringIO

from ipython_genutils.testing.decorators import onlyif
from ipython_genutils.tempdir import TemporaryDirectory
from jupyter_client import kernelspec

sample_kernel_json = {'argv':['cat', '{connection_file}'],
                      'display_name':'Test kernel',
                     }

class KernelSpecTests(unittest.TestCase):
    
    def _install_sample_kernel(self, kernels_dir):
        """install a sample kernel in a kernels directory"""
        sample_kernel_dir = pjoin(kernels_dir, 'Sample')
        os.makedirs(sample_kernel_dir)
        json_file = pjoin(sample_kernel_dir, 'kernel.json')
        with open(json_file, 'w') as f:
            json.dump(sample_kernel_json, f)
        return sample_kernel_dir
    
    def setUp(self):
        td = TemporaryDirectory()
        self.env_patch = patch.dict(os.environ, {
            'JUPYTER_CONFIG_DIR': pjoin(td.name, 'jupyter'),
            'JUPYTER_DATA_DIR': pjoin(td.name, 'jupyter_data'),
            'JUPYTER_RUNTIME_DIR': pjoin(td.name, 'jupyter_runtime'),
        })
        self.env_patch.start()
        self.addCleanup(td.cleanup)
        self.sample_kernel_dir = self._install_sample_kernel(
            pjoin(td.name, 'jupyter_data', 'kernels'))

        self.ksm = kernelspec.KernelSpecManager()

        td2 = TemporaryDirectory()
        self.addCleanup(td2.cleanup)
        self.installable_kernel = td2.name
        with open(pjoin(self.installable_kernel, 'kernel.json'), 'w') as f:
            json.dump(sample_kernel_json, f)

    def tearDown(self):
        self.env_patch.stop()

    def test_find_kernel_specs(self):
        kernels = self.ksm.find_kernel_specs()
        self.assertEqual(kernels['sample'], self.sample_kernel_dir)

    def test_get_kernel_spec(self):
        ks = self.ksm.get_kernel_spec('SAMPLE')  # Case insensitive
        self.assertEqual(ks.resource_dir, self.sample_kernel_dir)
        self.assertEqual(ks.argv, sample_kernel_json['argv'])
        self.assertEqual(ks.display_name, sample_kernel_json['display_name'])
        self.assertEqual(ks.env, {})
    
    def test_kernel_spec_priority(self):
        td = TemporaryDirectory()
        self.addCleanup(td.cleanup)
        sample_kernel = self._install_sample_kernel(td.name)
        self.ksm.kernel_dirs.append(td.name)
        kernels = self.ksm.find_kernel_specs()
        self.assertEqual(kernels['sample'], self.sample_kernel_dir)
        self.ksm.kernel_dirs.insert(0, td.name)
        kernels = self.ksm.find_kernel_specs()
        self.assertEqual(kernels['sample'], sample_kernel)

    def test_install_kernel_spec(self):
        self.ksm.install_kernel_spec(self.installable_kernel,
                                     kernel_name='tstinstalled',
                                     user=True)
        self.assertIn('tstinstalled', self.ksm.find_kernel_specs())
        
        # install again works
        self.ksm.install_kernel_spec(self.installable_kernel,
                                     kernel_name='tstinstalled',
                                     user=True)

    def test_install_kernel_spec_prefix(self):
        td = TemporaryDirectory()
        self.addCleanup(td.cleanup)
        capture = StringIO()
        handler = StreamHandler(capture)
        self.ksm.log.addHandler(handler)
        self.ksm.install_kernel_spec(self.installable_kernel,
                                     kernel_name='tstinstalled',
                                     prefix=td.name)
        captured = capture.getvalue()
        self.ksm.log.removeHandler(handler)
        self.assertIn("may not be found", captured)
        self.assertNotIn('tstinstalled', self.ksm.find_kernel_specs())

        # add prefix to path, so we find the spec
        self.ksm.kernel_dirs.append(pjoin(td.name, 'share', 'jupyter', 'kernels'))
        self.assertIn('tstinstalled', self.ksm.find_kernel_specs())
    
        # Run it again, no warning this time because we've added it to the path
        capture = StringIO()
        handler = StreamHandler(capture)
        self.ksm.log.addHandler(handler)
        self.ksm.install_kernel_spec(self.installable_kernel,
                                     kernel_name='tstinstalled',
                                     prefix=td.name)
        captured = capture.getvalue()
        self.ksm.log.removeHandler(handler)
        self.assertNotIn("may not be found", captured)

    @onlyif(os.name != 'nt' and not os.access('/usr/local/share', os.W_OK), "needs Unix system without root privileges")
    def test_cant_install_kernel_spec(self):
        with self.assertRaises(OSError):
            self.ksm.install_kernel_spec(self.installable_kernel,
                                         kernel_name='tstinstalled',
                                         user=False)
