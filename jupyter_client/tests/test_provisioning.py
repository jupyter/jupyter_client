"""Test Provisionering"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import os
import pytest
import sys

from jupyter_core import paths
from ..kernelspec import KernelSpecManager, NoSuchKernel
from ..manager import KernelManager, AsyncKernelManager
from ..provisioning import ClientProvisioner

pjoin = os.path.join


@pytest.fixture
def no_provisioner():
    kernel_dir = pjoin(paths.jupyter_data_dir(), 'kernels', 'no_provisioner')
    os.makedirs(kernel_dir)
    with open(pjoin(kernel_dir, 'kernel.json'), 'w') as f:
        f.write(json.dumps({
            'argv': [sys.executable,
                     '-m', 'jupyter_client.tests.signalkernel',
                     '-f', '{connection_file}'],
            'display_name': "Signal Test Kernel Default",
            'env': {'TEST_VARS': '${TEST_VARS}:test_var_2'}
        }))


@pytest.fixture
def default_provisioner():
    kernel_dir = pjoin(paths.jupyter_data_dir(), 'kernels', 'default_provisioner')
    os.makedirs(kernel_dir)
    with open(pjoin(kernel_dir, 'kernel.json'), 'w') as f:
        f.write(json.dumps({
            'argv': [sys.executable,
                     '-m', 'jupyter_client.tests.signalkernel',
                     '-f', '{connection_file}'],
            'display_name': "Signal Test Kernel w Provisioner",
            'env': {'TEST_VARS': '${TEST_VARS}:test_var_2'},
            'metadata': {
                'environment_provisioner': {
                    'provisioner_name': 'ClientProvisioner',
                    'config': {'config_var_1': 42, 'config_var_2': 'foo'}
                }
            }
        }))


@pytest.fixture
def missing_provisioner():
    kernel_dir = pjoin(paths.jupyter_data_dir(), 'kernels', 'missing_provisioner')
    os.makedirs(kernel_dir)
    with open(pjoin(kernel_dir, 'kernel.json'), 'w') as f:
        f.write(json.dumps({
            'argv': [sys.executable,
                     '-m', 'jupyter_client.tests.signalkernel',
                     '-f', '{connection_file}'],
            'display_name': "Signal Test Kernel Missing Provisioner",
            'env': {'TEST_VARS': '${TEST_VARS}:test_var_2'},
            'metadata': {
                'environment_provisioner': {
                    'provisioner_name': 'MissingProvisioner',
                    'config': {'config_var_1': 42, 'config_var_2': 'foo'}
                }
            }
        }))


@pytest.fixture
def ksm():
    return KernelSpecManager()


@pytest.fixture(params=['no_provisioner', 'default_provisioner', 'missing_provisioner'])
def akm(request, no_provisioner, missing_provisioner, default_provisioner):
    return AsyncKernelManager(kernel_name=request.param)


class TestDiscovery:
    def test_find_all_specs(self, no_provisioner, missing_provisioner, default_provisioner, ksm):
        kernels = ksm.get_all_specs()

        # Ensure specs for no_provisioner and default_provisioner exist and missing_provisioner doesn't
        assert 'no_provisioner' in kernels
        assert 'default_provisioner' in kernels
        assert 'missing_provisioner' not in kernels

    def test_get_missing(self, missing_provisioner, ksm):
        with pytest.raises(NoSuchKernel):
            ksm.get_kernel_spec('missing_provisioner')


class TestRuntime:

    @pytest.mark.asyncio
    async def test_async_lifecycle(self, akm):
        assert akm.provisioner is None
        if akm.kernel_name == 'missing_provisioner':
            with pytest.raises(NoSuchKernel):
                await akm.start_kernel()
        else:
            await akm.start_kernel()
            assert isinstance(akm.provisioner, ClientProvisioner)
            assert akm.kernel is akm.provisioner
            if akm.kernel_name == 'default_provisioner':
                assert akm.provisioner.config.get('config_var_1') == 42
                assert akm.provisioner.config.get('config_var_2') == 'foo'
            else:
                assert 'config_var_1' not in akm.provisioner.config
                assert 'config_var_2' not in akm.provisioner.config
            await akm.shutdown_kernel()
            assert akm.kernel is None
            assert akm.provisioner is None
