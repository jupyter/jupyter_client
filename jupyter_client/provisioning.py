"""Kernel Environment Provisioner Classes"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import signal
import sys

from entrypoints import get_group_all, EntryPoint
from typing import Optional, Dict, List, Any
from traitlets.config import LoggingConfigurable, SingletonConfigurable

from .launcher import launch_kernel

DEFAULT_PROVISIONER = "ClientProvisioner"


class EnvironmentProvisionerBase(LoggingConfigurable):  # TODO - determine name for base class
    """Base class defining methods for EnvironmentProvisioner classes.

       Theses methods model those of the Subprocess Popen class:
       https://docs.python.org/3/library/subprocess.html#popen-objects
    """

    def __init__(self, **kwargs):
        super(EnvironmentProvisionerBase, self).__init__(**kwargs)
        self.provisioner_config = kwargs.get('provisioner_config')

    def poll(self) -> [int, None]:
        """Checks if kernel process is still running.

         If running, None is returned, otherwise the process's integer-valued exit code is returned.
         """
        raise NotImplementedError()

    def wait(self, timeout: Optional[float] = None) -> [int, None]:
        """Waits for kernel process to terminate.  As a result, this method should be called with
        a value for timeout.

        If the kernel process does not terminate following timeout seconds, a TimeoutException will
        be raised - that can be caught and retried.  If the kernel process has terminated, its
        integer-valued exit code will be returned.
        """
        raise NotImplementedError()

    def send_signal(self, signum: int) -> None:
        """Sends signal identified by signum to the kernel process."""
        raise NotImplementedError()

    def kill(self) -> None:
        """Kills the kernel process.  This is typically accomplished via a SIGKILL signal, which
        cannot be caught.
        """
        raise NotImplementedError()

    def terminate(self) -> None:
        """Terminates the kernel process.  This is typically accomplished via a SIGTERM signal, which
        can be caught, allowing the kernel provisioner to perform possible cleanup of resources.
        """
        raise NotImplementedError()

    def cleanup(self) -> None:
        """Cleanup any resources allocated on behalf of the kernel provisioner."""
        raise NotImplementedError()

    def format_kernel_cmd(self, cmd: List[str], **kwargs: Dict[str, Any]) -> List[str]:
        """Replace any kernel provisioner-specific templated arguments in the launch command."""
        return cmd

    def pre_launch(self, cmd: List[str], **kwargs: Dict[str, Any]) -> None:
        """Perform any steps in preparation for kernel process launch."""
        pass

    def launch_kernel(self, cmd: List[str], **kwargs: Dict[str, Any]) -> 'EnvironmentProvisionerBase':
        """Launch the kernel process returning the class instance."""
        raise NotImplementedError()

    def post_launch(self) -> None:
        """Perform any steps following the kernel process launch."""
        pass

    def get_provisioner_info(self) -> Dict:
        """Captures the base information necessary for kernel persistence relative to the provisioner.

        The superclass method must always be called first to ensure proper ordering.  Since this is the
        most base class, no call to `super()` is necessary.
        """
        provisioner_info = {}
        return provisioner_info

    def load_provisioner_info(self, provisioner_info: Dict) -> None:
        """Loads the base information necessary for kernel persistence relative to the provisioner.

        The superclass method must always be called first to ensure proper ordering.  Since this is the
        most base class, no call to `super()` is necessary.
        """
        pass


class ClientProvisioner(EnvironmentProvisionerBase):  # TODO - determine name for default class

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.popen = None
        self.pid = None
        self.pgid = None
        self.ip = None  # TODO - assume local_ip?

    def launch_kernel(self, cmd, **kwargs):
        self.popen = launch_kernel(cmd, **kwargs)
        pgid = None
        if hasattr(os, "getpgid"):
            try:
                pgid = os.getpgid(self.popen.pid)
            except OSError:
                pass
        self.pid = self.popen.pid
        self.pgid = pgid
        return self

    def poll(self) -> [int, None]:
        if self.popen:
            return self.popen.poll()

    def wait(self, timeout: Optional[float] = None) -> [int, None]:
        if self.popen:
            return self.popen.wait(timeout=timeout)

    def send_signal(self, signum: int) -> None:
        """Sends a signal to the process group of the kernel (this
        usually includes the kernel and any subprocesses spawned by
        the kernel).

        Note that since only SIGTERM is supported on Windows, we will
        check if the desired signal is for interrupt and apply the
        applicable code on Windows in that case.
        """
        if self.popen:
            if signum == signal.SIGINT and sys.platform == 'win32':
                from .win_interrupt import send_interrupt
                send_interrupt(self.popen.win32_interrupt_event)
                return

            if self.pgid and hasattr(os, "killpg"):
                try:
                    os.killpg(self.pgid, signum)
                    return
                except OSError:
                    pass
            return self.popen.send_signal(signum)

    def kill(self) -> None:
        if self.popen:
            try:
                self.popen.kill()
            except OSError as e:
                # In Windows, we will get an Access Denied error if the process
                # has already terminated. Ignore it.
                if sys.platform == 'win32':
                    if e.winerror != 5:
                        raise
                # On Unix, we may get an ESRCH error if the process has already
                # terminated. Ignore it.
                else:
                    from errno import ESRCH
                    if e.errno != ESRCH:
                        raise

    def terminate(self) -> None:
        if self.popen:
            return self.popen.terminate()

    def cleanup(self) -> None:
        pass

    def get_provisioner_info(self) -> Dict:
        """Captures the base information necessary for kernel persistence relative to the provisioner.
        """
        provisioner_info = super(ClientProvisioner, self).get_provisioner_info()
        provisioner_info.update({'pid': self.pid, 'pgid': self.pgid, 'ip': self.ip})
        return provisioner_info

    def load_provisioner_info(self, provisioner_info: Dict) -> None:
        """Loads the base information necessary for kernel persistence relative to the provisioner.
        """
        super(ClientProvisioner, self).load_provisioner_info(provisioner_info)
        self.pid = provisioner_info['pid']
        self.pgid = provisioner_info['pgid']
        self.ip = provisioner_info['ip']


class EnvironmentProvisionerFactory(SingletonConfigurable):
    """EnvironmentProvisionerFactory is responsible for validating and initializing provisioner instances.
    """

    provisioners: Dict[str, EntryPoint] = {}

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        for ep in get_group_all('jupyter_client.environment_provisioners'):
            self.provisioners[ep.name] = ep

    def is_provisioner_available(self, kernel_spec: Dict[str, Any]) -> bool:
        """
        Reads the associated kernel_spec to determine the provisioner and returns whether it
        exists as an entry_point (True) or not (False).
        """
        provisioner_cfg = EnvironmentProvisionerFactory._get_provisioner_config(kernel_spec)
        provisioner_name = provisioner_cfg.get('provisioner_name')
        return provisioner_name in self.provisioners

    def create_provisioner_instance(self, kernel_spec: Dict[str, Any]) -> EnvironmentProvisionerBase:
        """
        Reads the associated kernel_spec and to see if has an environment_provisioner stanza.
        If one exists, it instantiates an instance.  If an environment provisioner is not
        specified in the kernelspec, a DEFAULT_PROVISIONER stanza is fabricated and instantiated.
        The instantiated instance is returned.

        If the provisioner is found to not exist (not registered via entry_points),
        ModuleNotFoundError is raised.
        """
        provisioner_cfg = EnvironmentProvisionerFactory._get_provisioner_config(kernel_spec)
        provisioner_name = provisioner_cfg.get('provisioner_name')
        if provisioner_name not in self.provisioners:
            raise ModuleNotFoundError(f"Environment provisioner '{provisioner_name}' has not been registered.")

        self.log.debug("Instantiating kernel '{}' with environment provisioner: {}".
                       format(kernel_spec.get('display_name'), provisioner_name))
        provisioner_class = self.provisioners[provisioner_name].load()
        provisioner_config = provisioner_cfg.get('config')
        return provisioner_class(parent=self.parent, **provisioner_config)

    @staticmethod
    def _get_provisioner_config(kernel_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return the environment_provisioner stanza from the kernel_spec.

        Checks the kernel_spec's metadata dictionary for an environment_provisioner entry.
        If found, it is returned, else one is created relative to the DEFAULT_PROVISIONER and returned.

        Parameters
        ----------
        kernel_spec : Dict
            The kernel specification object from which the provisioner dictionary is derived.

        Returns
        -------
        dict
            The provisioner portion of the kernel_spec.  If one does not exist, it will contain the default
            information.  If no `config` sub-dictionary exists, an empty `config` dictionary will be added.

        """
        if kernel_spec:
            metadata = kernel_spec.get('metadata', {})
            if 'environment_provisioner' in metadata:
                env_provisioner = metadata.get('environment_provisioner')
                if 'provisioner_name' in env_provisioner:  # If no provisioner_name, return default
                    if 'config' not in env_provisioner:  # if provisioner_name, but no config stanza, add one
                        env_provisioner.update({"config": {}})
                    return env_provisioner  # Return what we found (plus config stanza if necessary)
        return {"provisioner_name": DEFAULT_PROVISIONER, "config": {}}
