"""Kernel Provisioner Classes"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import os
from typing import Any
from typing import Dict
from typing import List

from entrypoints import EntryPoint  # type: ignore
from entrypoints import get_group_all
from entrypoints import get_single
from entrypoints import NoSuchEntryPoint
from traitlets.config import default  # type: ignore
from traitlets.config import SingletonConfigurable
from traitlets.config import Unicode

from .provisioner_base import KernelProvisionerBase


class KernelProvisionerFactory(SingletonConfigurable):
    """KernelProvisionerFactory is responsible for creating provisioner instances."""

    GROUP_NAME = 'jupyter_client.kernel_provisioners'
    provisioners: Dict[str, EntryPoint] = {}

    default_provisioner_name_env = "JUPYTER_DEFAULT_PROVISIONER_NAME"
    default_provisioner_name = Unicode(
        config=True,
        help="""Indicates the name of the provisioner to use when no kernel_provisioner
                                       entry is present in the kernelspec.""",
    )

    @default('default_provisioner_name')
    def default_provisioner_name_default(self):
        return os.getenv(self.default_provisioner_name_env, "local-provisioner")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        for ep in KernelProvisionerFactory._get_all_provisioners():
            self.provisioners[ep.name] = ep

    def is_provisioner_available(self, kernel_name: str, kernel_spec: Any) -> bool:
        """
        Reads the associated kernel_spec to determine the provisioner and returns whether it
        exists as an entry_point (True) or not (False).  If the referenced provisioner is not
        in the current set of provisioners, attempt to retrieve its entrypoint.  If found, add
        to the list, else catch exception and return false.
        """
        is_available: bool = True
        provisioner_cfg = self._get_provisioner_config(kernel_spec)
        provisioner_name = str(provisioner_cfg.get('provisioner_name'))
        if provisioner_name not in self.provisioners:
            try:
                ep = KernelProvisionerFactory._get_provisioner(provisioner_name)
                self.provisioners[provisioner_name] = ep  # Update cache
            except NoSuchEntryPoint:
                is_available = False
                self.log.warning(
                    f"Kernel '{kernel_name}' is referencing a kernel provisioner "
                    f"('{provisioner_name}') that is not available.  Ensure the "
                    f"appropriate package has been installed and retry."
                )
        return is_available

    def create_provisioner_instance(
        self, kernel_id: str, kernel_spec: Any
    ) -> KernelProvisionerBase:
        """
        Reads the associated kernel_spec and to see if has a kernel_provisioner stanza.
        If one exists, it instantiates an instance.  If a kernel provisioner is not
        specified in the kernelspec, a DEFAULT_PROVISIONER stanza is fabricated and instantiated.
        The instantiated instance is returned.

        If the provisioner is found to not exist (not registered via entry_points),
        ModuleNotFoundError is raised.
        """
        provisioner_cfg = self._get_provisioner_config(kernel_spec)
        provisioner_name = provisioner_cfg.get('provisioner_name')
        if provisioner_name not in self.provisioners:
            raise ModuleNotFoundError(
                f"Kernel provisioner '{provisioner_name}' has not been registered."
            )

        self.log.debug(
            f"Instantiating kernel '{kernel_spec.display_name}' with "
            f"kernel provisioner: {provisioner_name}"
        )
        provisioner_class = self.provisioners[provisioner_name].load()
        provisioner_config = provisioner_cfg.get('config')
        return provisioner_class(
            kernel_id=kernel_id, kernel_spec=kernel_spec, parent=self.parent, **provisioner_config
        )

    def _get_provisioner_config(self, kernel_spec: Any) -> Dict[str, Any]:
        """
        Return the kernel_provisioner stanza from the kernel_spec.

        Checks the kernel_spec's metadata dictionary for a kernel_provisioner entry.
        If found, it is returned, else one is created relative to the DEFAULT_PROVISIONER
        and returned.

        Parameters
        ----------
        kernel_spec : Any - this is a KernelSpec type but listed as Any to avoid circular import
            The kernel specification object from which the provisioner dictionary is derived.

        Returns
        -------
        dict
            The provisioner portion of the kernel_spec.  If one does not exist, it will contain
            the default information.  If no `config` sub-dictionary exists, an empty `config`
            dictionary will be added.
        """
        env_provisioner = kernel_spec.metadata.get('kernel_provisioner', {})
        if 'provisioner_name' in env_provisioner:  # If no provisioner_name, return default
            if (
                'config' not in env_provisioner
            ):  # if provisioner_name, but no config stanza, add one
                env_provisioner.update({"config": {}})
            return env_provisioner  # Return what we found (plus config stanza if necessary)
        return {"provisioner_name": self.default_provisioner_name, "config": {}}

    @staticmethod
    def _get_all_provisioners() -> List[EntryPoint]:
        """Wrapper around entrypoints.get_group_all() - primarily to facilitate testing."""
        return get_group_all(KernelProvisionerFactory.GROUP_NAME)

    @staticmethod
    def _get_provisioner(name: str) -> EntryPoint:
        """Wrapper around entrypoints.get_single() - primarily to facilitate testing."""
        return get_single(KernelProvisionerFactory.GROUP_NAME, name)
