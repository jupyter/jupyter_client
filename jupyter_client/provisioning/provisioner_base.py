"""Kernel Provisioner Classes"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import os
from abc import ABC
from abc import ABCMeta
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from traitlets.config import Instance  # type: ignore
from traitlets.config import LoggingConfigurable
from traitlets.config import Unicode


class KernelProvisionerMeta(ABCMeta, type(LoggingConfigurable)):  # type: ignore
    pass


class KernelProvisionerBase(ABC, LoggingConfigurable, metaclass=KernelProvisionerMeta):
    """Base class defining methods for KernelProvisioner classes.

    Theses methods model those of the Subprocess Popen class:
    https://docs.python.org/3/library/subprocess.html#popen-objects
    """

    # The kernel specification associated with this provisioner
    kernel_spec: Any = Instance('jupyter_client.kernelspec.KernelSpec', allow_none=True)
    kernel_id: str = Unicode(None, allow_none=True)
    _connection_info: dict = {}

    @property
    def connection_info(self) -> Dict[str, Any]:
        """Returns the connection information relative to this provisioner's managed instance"""
        return self._connection_info

    @property
    @abstractmethod
    def has_process(self) -> bool:
        """Returns true if this provisioner is currently managing a process."""
        pass

    @abstractmethod
    async def poll(self) -> Optional[int]:
        """Checks if kernel process is still running.

        If running, None is returned, otherwise the process's integer-valued exit code is returned.
        """
        pass

    @abstractmethod
    async def wait(self) -> Optional[int]:
        """Waits for kernel process to terminate."""
        pass

    @abstractmethod
    async def send_signal(self, signum: int) -> None:
        """Sends signal identified by signum to the kernel process."""
        pass

    @abstractmethod
    async def kill(self, restart: bool = False) -> None:
        """Kills the kernel process.  This is typically accomplished via a SIGKILL signal,
        which cannot be caught.

        restart is True if this operation precedes a start launch_kernel request.
        """
        pass

    @abstractmethod
    async def terminate(self, restart: bool = False) -> None:
        """Terminates the kernel process.  This is typically accomplished via a SIGTERM signal,
        which can be caught, allowing the kernel provisioner to perform possible cleanup
        of resources.

        restart is True if this operation precedes a start launch_kernel request.
        """
        pass

    @abstractmethod
    async def launch_kernel(self, cmd: List[str], **kwargs: Any) -> None:
        """Launch the kernel process. """
        pass

    @abstractmethod
    async def cleanup(self, restart: bool = False) -> None:
        """Cleanup any resources allocated on behalf of the kernel provisioner.

        restart is True if this operation precedes a start launch_kernel request.
        """
        pass

    async def shutdown_requested(self, restart: bool = False) -> None:
        """Called after KernelManager sends a `shutdown_request` message to kernel.

        This method is optional and is primarily used in scenarios where the provisioner
        communicates with a sibling (nanny) process to the kernel.
        """
        pass

    async def pre_launch(self, **kwargs: Any) -> Dict[str, Any]:
        """Perform any steps in preparation for kernel process launch.

        This includes applying additional substitutions to the kernel launch command and env.
        It also includes preparation of launch parameters.

        Returns potentially updated kwargs.
        """
        env = kwargs.pop('env', os.environ).copy()
        env.update(self.__apply_env_substitutions(env))
        self._finalize_env(env)
        kwargs['env'] = env

        return kwargs

    async def post_launch(self, **kwargs: Any) -> None:
        """Perform any steps following the kernel process launch."""
        pass

    async def get_provisioner_info(self) -> Dict[str, Any]:
        """Captures the base information necessary for persistence relative to this instance.

        The superclass method must always be called first to ensure proper ordering.
        """
        provisioner_info: Dict[str, Any] = dict()
        provisioner_info['kernel_id'] = self.kernel_id
        provisioner_info['connection_info'] = self.connection_info
        return provisioner_info

    async def load_provisioner_info(self, provisioner_info: Dict) -> None:
        """Loads the base information necessary for persistence relative to this instance.

        The superclass method must always be called first to ensure proper ordering.
        """
        self.kernel_id = provisioner_info['kernel_id']
        self._connection_info = provisioner_info['connection_info']

    def get_shutdown_wait_time(self, recommended: float = 5.0) -> float:
        """Returns the time allowed for a complete shutdown.  This may vary by provisioner.

        The recommended value will typically be what is configured in the kernel manager.
        """
        return recommended

    def _finalize_env(self, env: Dict[str, str]) -> None:
        """Ensures env is appropriate prior to launch.

        Subclasses should be sure to call super()._finalize_env(env)
        """
        if self.kernel_spec.language and self.kernel_spec.language.lower().startswith("python"):
            # Don't allow PYTHONEXECUTABLE to be passed to kernel process.
            # If set, it can bork all the things.
            env.pop('PYTHONEXECUTABLE', None)

    def __apply_env_substitutions(self, substitution_values: Dict[str, str]):
        """Walks entries in the kernelspec's env stanza and applies substitutions from current env.

        Returns the substituted list of env entries.
        Note: This method is private and is not intended to be overridden by provisioners.
        """
        substituted_env = {}
        if self.kernel_spec:
            from string import Template

            # For each templated env entry, fill any templated references
            # matching names of env variables with those values and build
            # new dict with substitutions.
            templated_env = self.kernel_spec.env
            for k, v in templated_env.items():
                substituted_env.update({k: Template(v).safe_substitute(substitution_values)})
        return substituted_env
