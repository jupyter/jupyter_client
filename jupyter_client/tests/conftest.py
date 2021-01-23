"""Pytest fixtures and configuration"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import pytest

from jupyter_core import paths
from .utils import test_env

pjoin = os.path.join


@pytest.fixture(autouse=True)
def env():
    env_patch = test_env()
    env_patch.start()
    yield
    env_patch.stop()


@pytest.fixture()
def kernel_dir():
    return pjoin(paths.jupyter_data_dir(), 'kernels')