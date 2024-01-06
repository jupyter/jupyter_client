import gc
import os

import pytest

from jupyter_client.utils import ensure_event_loop

# Must be set before importing from `jupyter_core`.
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"


pytest_plugins = ["pytest_jupyter", "pytest_jupyter.jupyter_client"]


@pytest.fixture(autouse=True)
def setup_environ(jp_environ):
    yield
    ensure_event_loop().close()
    gc.collect()
