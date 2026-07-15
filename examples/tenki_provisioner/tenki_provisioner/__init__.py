"""Tenki Sandbox kernel provisioner for jupyter_client.

Launch Jupyter kernels inside disposable `Tenki Sandbox <https://tenki.cloud>`_
microVMs. Register the provisioner in a kernelspec's ``kernel_provisioner``
metadata under the name ``tenki-provisioner``.
"""

from .provisioner import REMOTE_HOME, TenkiProvisioner

__all__ = ["REMOTE_HOME", "TenkiProvisioner"]
__version__ = "0.1.0"
