import asyncio
import os

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # type:ignore

import pytest

# Must be set before importing from `jupyter_core`.
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"


pytest_plugins = ["pytest_jupyter", "pytest_jupyter.jupyter_client"]


def pytest_addoption(parser):
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="run tests marked as slow",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(autouse=True)
def setup_environ(jp_environ):
    pass
