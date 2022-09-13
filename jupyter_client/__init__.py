"""Client-side implementations of the Jupyter protocol"""
import pathlib

from ._version import __version__  # noqa
from ._version import protocol_version  # noqa
from ._version import protocol_version_info  # noqa
from ._version import version_info  # noqa

JUPYTER_CLIENT_EVENTS_URI = "https://events.jupyter.org/jupyter_client"
DEFAULT_EVENTS_SCHEMA_PATH = pathlib.Path(__file__).parent / "event_schemas"

try:
    from .asynchronous import AsyncKernelClient  # noqa
    from .blocking import BlockingKernelClient  # noqa
    from .client import KernelClient  # noqa
    from .connect import *  # noqa
    from .launcher import *  # noqa
    from .manager import AsyncKernelManager  # noqa
    from .manager import KernelManager  # noqa
    from .manager import run_kernel  # noqa
    from .multikernelmanager import AsyncMultiKernelManager  # noqa
    from .multikernelmanager import MultiKernelManager  # noqa
    from .provisioning import KernelProvisionerBase  # noqa
    from .provisioning import LocalProvisioner  # noqa
except ModuleNotFoundError:
    import warnings

    warnings.warn("Could not import submodules")
