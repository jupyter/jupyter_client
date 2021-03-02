"""Kernel Provisioner Classes"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import asyncio
import os
import signal
import sys

from abc import ABCMeta, ABC, abstractmethod
from entrypoints import EntryPoint, get_group_all, get_single, NoSuchEntryPoint
from typing import Optional, Dict, List, Any, Tuple
from traitlets.config import Config, default, Instance, LoggingConfigurable, SingletonConfigurable, Unicode

from .connect import write_connection_file
from .launcher import async_launch_kernel
from .localinterfaces import is_local_ip, local_ips


class KernelProvisionerMeta(ABCMeta, type(LoggingConfigurable)):
    pass


class KernelProvisionerBase(ABC, LoggingConfigurable, metaclass=KernelProvisionerMeta):
    """Base class defining methods for KernelProvisioner classes.

       Theses methods model those of the Subprocess Popen class:
       https://docs.python.org/3/library/subprocess.html#popen-objects
    """
    # The kernel specification associated with this provisioner
    kernel_spec: Any = Instance('jupyter_client.kernelspec.KernelSpec', allow_none=True)
    kernel_id: str = Unicode(None, allow_none=True)
    connection_info: dict = {}

    @abstractmethod
    async def poll(self) -> [int, None]:
        """Checks if kernel process is still running.

         If running, None is returned, otherwise the process's integer-valued exit code is returned.
         """
        pass

    @abstractmethod
    async def wait(self) -> [int, None]:
        """Waits for kernel process to terminate."""
        pass

    @abstractmethod
    async def send_signal(self, signum: int) -> None:
        """Sends signal identified by signum to the kernel process."""
        pass

    @abstractmethod
    async def kill(self, restart=False) -> None:
        """Kills the kernel process.  This is typically accomplished via a SIGKILL signal, which
        cannot be caught.

        restart is True if this operation precedes a start launch_kernel request.
        """
        pass

    @abstractmethod
    async def terminate(self, restart=False) -> None:
        """Terminates the kernel process.  This is typically accomplished via a SIGTERM signal, which
        can be caught, allowing the kernel provisioner to perform possible cleanup of resources.

        restart is True if this operation precedes a start launch_kernel request.
        """
        pass

    @abstractmethod
    async def launch_kernel(self, cmd: List[str], **kwargs: Any) -> Tuple['KernelProvisionerBase', Dict]:
        """Launch the kernel process returning the class instance and connection info."""
        pass

    @abstractmethod
    async def cleanup(self, restart=False) -> None:
        """Cleanup any resources allocated on behalf of the kernel provisioner.

        restart is True if this operation precedes a start launch_kernel request.
        """
        pass

    async def pre_launch(self, **kwargs: Any) -> Dict[str, Any]:
        """Perform any steps in preparation for kernel process launch.

        This includes applying additional substitutions to the kernel launch command and env.
        It also includes preparation of launch parameters.

        Returns potentially updated kwargs.
        """

        env = kwargs.pop('env', os.environ).copy()

        env.update(self._apply_env_substitutions(env))

        self._validate_parameters(env, **kwargs)

        self._finalize_env(env)

        kwargs['env'] = env

        return kwargs

    async def post_launch(self, **kwargs: Any) -> None:
        """Perform any steps following the kernel process launch."""
        pass

    async def get_provisioner_info(self) -> Dict:
        """Captures the base information necessary for kernel persistence relative to the provisioner.

        The superclass method must always be called first to ensure proper ordering.  Since this is the
        most base class, no call to `super()` is necessary.
        """
        provisioner_info = {}
        return provisioner_info

    async def load_provisioner_info(self, provisioner_info: Dict) -> None:
        """Loads the base information necessary for kernel persistence relative to the provisioner.

        The superclass method must always be called first to ensure proper ordering.  Since this is the
        most base class, no call to `super()` is necessary.
        """
        pass

    def get_shutdown_wait_time(self, recommended: Optional[float] = 5.0) -> float:
        """Returns the time allowed for a complete shutdown.  This may vary by provisioner.

        The recommended value will typically be what is configured in the kernel manager.
        """
        return recommended

    def _apply_env_substitutions(self, substitution_values: Dict[str, str]):
        """ Walks env entries in the kernelspec's env stanza and applies possible substitutions from current env
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

    def _finalize_env(self, env: Dict[str, str]) -> None:
        """ Ensures env is appropriate prior to launch. """

        if self.kernel_spec.language and self.kernel_spec.language.lower().startswith("python"):
            # Don't allow PYTHONEXECUTABLE to be passed to kernel process.
            # If set, it can bork all the things.
            env.pop('PYTHONEXECUTABLE', None)

    def _validate_parameters(self, env: Dict[str, str], **kwargs: Any) -> None:
        """Future: Validates that launch parameters adhere to schema specified in kernel specification."""
        pass


class LocalProvisioner(KernelProvisionerBase):

    process = None
    async_subprocess = None
    _exit_future = None
    pid = None
    pgid = None

    async def poll(self) -> [int, None]:
        if self.process:
            if self.async_subprocess:
                if not self._exit_future.done():  # adhere to process returncode
                    return None
            else:
                if self.process.poll() is None:
                    return None
        return False

    async def wait(self) -> [int, None]:
        if self.process:
            if self.async_subprocess:
                await self.process.wait()
            else:
                # Use busy loop at 100ms intervals, polling until the process is
                # not alive.  If we find the process is no longer alive, complete
                # its cleanup via the blocking wait().  Callers are responsible for
                # issuing calls to wait() using a timeout (see kill()).
                while await self.poll() is None:
                    await asyncio.sleep(0.1)

                # Process is no longer alive, wait and clear
                self.process.wait()
                self.process = None

    async def send_signal(self, signum: int) -> None:
        """Sends a signal to the process group of the kernel (this
        usually includes the kernel and any subprocesses spawned by
        the kernel).

        Note that since only SIGTERM is supported on Windows, we will
        check if the desired signal is for interrupt and apply the
        applicable code on Windows in that case.
        """
        if self.process:
            if signum == signal.SIGINT and sys.platform == 'win32':
                from .win_interrupt import send_interrupt
                send_interrupt(self.process.win32_interrupt_event)
                return

            # Prefer process-group over process
            if self.pgid and hasattr(os, "killpg"):
                try:
                    os.killpg(self.pgid, signum)
                    return
                except OSError:
                    pass
            return self.process.send_signal(signum)

    async def kill(self, restart=False) -> None:
        if self.process:
            try:
                self.process.kill()
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

    async def terminate(self, restart=False) -> None:
        if self.process:
            return self.process.terminate()

    async def cleanup(self, restart=False) -> None:
        pass

    async def pre_launch(self, **kwargs: Any) -> Dict[str, Any]:
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
            km._launch_args = kwargs.copy()
            # build the Popen cmd
            extra_arguments = kwargs.pop('extra_arguments', [])

            # write connection file / get default ports
            km.write_connection_file()  # TODO - this will need to change when handshake pattern is adopted
            self.connection_info = km.get_connection_info()

            kernel_cmd = km.format_kernel_cmd(extra_arguments=extra_arguments)  # This needs to remain here for b/c
        else:
            extra_arguments = kwargs.pop('extra_arguments', [])
            kernel_cmd = self.kernel_spec.argv + extra_arguments

        return await super().pre_launch(cmd=kernel_cmd, **kwargs)

    async def launch_kernel(self, cmd: List[str], **kwargs: Any) -> Tuple['LocalProvisioner', Dict]:
        scrubbed_kwargs = LocalProvisioner.scrub_kwargs(kwargs)
        self.process = await async_launch_kernel(cmd, **scrubbed_kwargs)
        self.async_subprocess = isinstance(self.process, asyncio.subprocess.Process)
        if self.async_subprocess:
            self._exit_future = asyncio.ensure_future(self.process.wait())
        pgid = None
        if hasattr(os, "getpgid"):
            try:
                pgid = os.getpgid(self.process.pid)
            except OSError:
                pass

        self.pid = self.process.pid
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
        provisioner_info = super(LocalProvisioner, self).get_provisioner_info()
        provisioner_info.update({'pid': self.pid, 'pgid': self.pgid, 'ip': self.ip})
        return provisioner_info

    def load_provisioner_info(self, provisioner_info: Dict) -> None:
        """Loads the base information necessary for kernel persistence relative to the provisioner.
        """
        super(LocalProvisioner, self).load_provisioner_info(provisioner_info)
        self.pid = provisioner_info['pid']
        self.pgid = provisioner_info['pgid']
        self.ip = provisioner_info['ip']


class KernelProvisionerFactory(SingletonConfigurable):
    """KernelProvisionerFactory is responsible for validating and initializing provisioner instances."""

    GROUP_NAME = 'jupyter_client.kernel_provisioners'
    provisioners: Dict[str, EntryPoint] = {}

    default_provisioner_name_env = "JUPYTER_DEFAULT_PROVISIONER_NAME"
    default_provisioner_name = Unicode(config=True,
                                       help="""Indicates the name of the provisioner to use when no kernel_provisioner
                                       entry is present in the kernelspec.""")

    @default('default_provisioner_name')
    def default_provisioner_name_default(self):
        return os.getenv(self.default_provisioner_name_env, "LocalProvisioner")

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
        provisioner_name = provisioner_cfg.get('provisioner_name')
        if provisioner_name not in self.provisioners:
            try:
                ep = KernelProvisionerFactory._get_provisioner(provisioner_name)
                self.provisioners[provisioner_name] = ep  # Update cache
            except NoSuchEntryPoint:
                is_available = False
                self.log.warning(
                    f"Kernel '{kernel_name}' is referencing a kernel provisioner ('{provisioner_name}') "
                    f"that is not available.  Ensure the appropriate package has been installed and retry.")
        return is_available

    def create_provisioner_instance(self, kernel_id: str, kernel_spec: Any) -> KernelProvisionerBase:
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
            raise ModuleNotFoundError(f"Kernel provisioner '{provisioner_name}' has not been registered.")

        self.log.debug(f"Instantiating kernel '{kernel_spec.display_name}' with "
                       f"kernel provisioner: {provisioner_name}")
        provisioner_class = self.provisioners[provisioner_name].load()
        provisioner_config = provisioner_cfg.get('config')
        return provisioner_class(kernel_id=kernel_id,
                                 kernel_spec=kernel_spec,
                                 parent=self.parent,
                                 **provisioner_config)

    def _get_provisioner_config(self, kernel_spec: Any) -> Dict[str, Any]:
        """
        Return the kernel_provisioner stanza from the kernel_spec.

        Checks the kernel_spec's metadata dictionary for a kernel_provisioner entry.
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
        env_provisioner = kernel_spec.metadata.get('kernel_provisioner', {})
        if 'provisioner_name' in env_provisioner:  # If no provisioner_name, return default
            if 'config' not in env_provisioner:  # if provisioner_name, but no config stanza, add one
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
