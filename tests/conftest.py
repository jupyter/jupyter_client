import os

import pytest

# Must be set before importing from `jupyter_core`.
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"


pytest_plugins = ["pytest_jupyter", "pytest_jupyter.jupyter_client"]


@pytest.fixture(autouse=True)
def setup_environ(jp_environ):
    pass
