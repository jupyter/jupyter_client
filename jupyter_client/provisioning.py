"""Kernel Environment Provisioner Classes"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import signal
import sys

from entrypoints import EntryPoint, get_group_all, get_single, NoSuchEntryPoint
from typing import Optional, Dict, List, Any, Tuple
from traitlets.config import Config, LoggingConfigurable, SingletonConfigurable

from .connect import write_connection_file
from .launcher import launch_kernel
from .localinterfaces import is_local_ip, local_ips

DEFAULT_PROVISIONER = "ClientProvisioner"


class EnvironmentProvisionerBase(LoggingConfigurable):  # TODO - determine name for base class
    """Base class defining methods for EnvironmentProvisioner classes.

       Theses methods model those of the Subprocess Popen class:
       https://docs.python.org/3/library/subprocess.html#popen-objects
    """
    # The kernel specification associated with this provisioner
    kernel_spec: Any
    kernel_id: str

    def __init__(self, **kwargs):
        # Pop off expected arguments...
        self.kernel_spec = kwargs.pop('kernel_spec', None)
        self.kernel_id = kwargs.pop('kernel_id', None)
        super().__init__(**kwargs)

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

    def pre_launch(self, **kwargs: Any) -> Dict[str, Any]:
        """Perform any steps in preparation for kernel process launch.

        This includes applying additional substitutions to the kernel launch command and env.
        It also includes preparation of launch parameters.

        Returns potentially updated kwargs.
        """

        env = kwargs.pop('env', os.environ).copy()
        # Don't allow PYTHONEXECUTABLE to be passed to kernel process.
        # If set, it can bork all the things.
        env.pop('PYTHONEXECUTABLE', None)

        env.update(self._get_env_substitutions(env))

        self._validate_parameters(env, **kwargs)

        kwargs['env'] = env

        return kwargs

    def _validate_parameters(self, env: Dict[str, Any], **kwargs: Any) -> None:
        """Future: Validates that launch parameters adhere to schema specified in kernel specification."""
        pass

    def launch_kernel(self, cmd: List[str], **kwargs: Any) -> Tuple['EnvironmentProvisionerBase', Dict]:
        """Launch the kernel process returning the class instance and connection info."""
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

    def _get_env_substitutions(self, substitution_values):
        """ Walks env entries in templated_env and applies possible substitutions from current env
            (represented by substitution_values).
            Returns the substituted list of env entries.
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


class ClientProvisioner(EnvironmentProvisionerBase):  # TODO - determine name for default class

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.popen = None
        self.pid = None
        self.pgid = None
        self.connection_info = {}

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

    def pre_launch(self, **kwargs: Any) -> Dict[str, Any]:
        """Perform any steps in preparation for kernel process launch.

        This includes applying additional substitutions to the kernel launch command and env.
        It also includes preparation of launch parameters.

        Returns the updated kwargs.
        """

        # If we have a kernel_manager pop it out of the args and use it to retain b/c.
        # This should be considered temporary until a better division of labor can be defined.
        km = kwargs.pop('kernel_manager')
        if km:
            if km.transport == 'tcp' and not is_local_ip(km.ip):
                raise RuntimeError("Can only launch a kernel on a local interface. "
                                   "This one is not: %s."
                                   "Make sure that the '*_address' attributes are "
                                   "configured properly. "
                                   "Currently valid addresses are: %s" % (km.ip, local_ips())
                                   )

            # save kwargs for use in restart
            km._launch_args = kwargs.copy()  # TODO - stash these on provisioner?
            # build the Popen cmd
            extra_arguments = kwargs.pop('extra_arguments', [])

            # write connection file / get default ports
            km.write_connection_file()  # TODO - this will need to change when handshake pattern is adopted
            self.connection_info = km.get_connection_info()

            kernel_cmd = km.format_kernel_cmd(extra_arguments=extra_arguments)  # This needs to remain here for b/c
        else:
            extra_arguments = kwargs.pop('extra_arguments', [])
            kernel_cmd = self.kernel_spec.argv + extra_arguments

        return super().pre_launch(cmd=kernel_cmd, **kwargs)

    def launch_kernel(self, cmd: List[str], **kwargs: Any) -> Tuple['ClientProvisioner', Dict]:
        scrubbed_kwargs = ClientProvisioner.scrub_kwargs(kwargs)
        self.popen = launch_kernel(cmd, **scrubbed_kwargs)
        pgid = None
        if hasattr(os, "getpgid"):
            try:
                pgid = os.getpgid(self.popen.pid)
            except OSError:
                pass
        self.pid = self.popen.pid
        self.pgid = pgid
        return self, self.connection_info

    @staticmethod
    def scrub_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Remove any keyword arguments that Popen does not tolerate."""
        keywords_to_scrub: List[str] = ['extra_arguments', 'kernel_id', 'kernel_manager']
        scrubbed_kwargs = kwargs.copy()
        for kw in keywords_to_scrub:
            scrubbed_kwargs.pop(kw, None)
        return scrubbed_kwargs

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

    GROUP_NAME = 'jupyter_client.environment_provisioners'
    provisioners: Dict[str, EntryPoint] = {}

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        for ep in get_group_all(EnvironmentProvisionerFactory.GROUP_NAME):
            self.provisioners[ep.name] = ep

    def is_provisioner_available(self, kernel_name: str, kernel_spec: Any) -> bool:
        """
        Reads the associated kernel_spec to determine the provisioner and returns whether it
        exists as an entry_point (True) or not (False).  If the referenced provisioner is not
        in the current set of provisioners, attempt to retrieve its entrypoint.  If found, add
        to the list, else catch exception and return false.
        """
        is_available: bool = True
        provisioner_cfg = EnvironmentProvisionerFactory._get_provisioner_config(kernel_spec)
        provisioner_name = provisioner_cfg.get('provisioner_name')
        if provisioner_name not in self.provisioners:
            try:
                ep = get_single(EnvironmentProvisionerFactory.GROUP_NAME, provisioner_name)
                self.provisioners[provisioner_name] = ep  # Update cache
            except NoSuchEntryPoint:
                is_available = False
                self.log.warning(
                    f"Kernel '{kernel_name}' is referencing an environment provisioner ('{provisioner_name}') "
                    f"that is not available.  Ensure the appropriate package has been installed and retry.")
        return is_available

    def create_provisioner_instance(self, kernel_id: str, kernel_spec: Any) -> EnvironmentProvisionerBase:
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

        self.log.debug(f"Instantiating kernel '{kernel_spec.display_name}' with "
                       f"environment provisioner: {provisioner_name}")
        provisioner_class = self.provisioners[provisioner_name].load()
        provisioner_config = provisioner_cfg.get('config')
        return provisioner_class(parent=self.parent,
                                 kernel_id=kernel_id,
                                 kernel_spec=kernel_spec,
                                 config=Config(provisioner_config))

    @staticmethod
    def _get_provisioner_config(kernel_spec: Any) -> Dict[str, Any]:
        """
        Return the environment_provisioner stanza from the kernel_spec.

        Checks the kernel_spec's metadata dictionary for an environment_provisioner entry.
        If found, it is returned, else one is created relative to the DEFAULT_PROVISIONER and returned.

        Parameters
        ----------
        kernel_spec : Any - this is a KernelSpec type but listed as Any to avoid circular import
            The kernel specification object from which the provisioner dictionary is derived.

        Returns
        -------
        dict
            The provisioner portion of the kernel_spec.  If one does not exist, it will contain the default
            information.  If no `config` sub-dictionary exists, an empty `config` dictionary will be added.

        """
        env_provisioner = kernel_spec.metadata.get('environment_provisioner', {})
        if 'provisioner_name' in env_provisioner:  # If no provisioner_name, return default
            if 'config' not in env_provisioner:  # if provisioner_name, but no config stanza, add one
                env_provisioner.update({"config": {}})
            return env_provisioner  # Return what we found (plus config stanza if necessary)
        return {"provisioner_name": DEFAULT_PROVISIONER, "config": {}}