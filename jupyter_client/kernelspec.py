"""Tools for managing kernel specs"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import json
import os
import re
import shutil
import typing as t
import warnings

from jupyter_core.paths import SYSTEM_JUPYTER_PATH, jupyter_data_dir, jupyter_path
from traitlets import Bool, CaselessStrEnum, Dict, HasTraits, List, Set, Type, Unicode, observe
from traitlets.config import LoggingConfigurable

from .provisioning import KernelProvisionerFactory as KPF  # noqa

pjoin = os.path.join

NATIVE_KERNEL_NAME = "python3"


class KernelSpec(HasTraits):
    """A kernel spec model object."""

    argv: List[str] = List()
    name = Unicode()
    mimetype = Unicode()
    display_name = Unicode()
    language = Unicode()
    env = Dict()
    resource_dir = Unicode()
    interrupt_mode = CaselessStrEnum(["message", "signal"], default_value="signal")
    metadata = Dict()

    @classmethod
    def from_resource_dir(cls: type[KernelSpec], resource_dir: str) -> KernelSpec:
        """Create a KernelSpec object by reading kernel.json

        Pass the path to the *directory* containing kernel.json.
        """
        kernel_file = pjoin(resource_dir, "kernel.json")
        with open(kernel_file, encoding="utf-8") as f:
            kernel_dict = json.load(f)
        return cls(resource_dir=resource_dir, **kernel_dict)

    def to_dict(self) -> dict[str, t.Any]:
        """Convert the kernel spec to a dict."""
        d = {
            "argv": self.argv,
            "env": self.env,
            "display_name": self.display_name,
            "language": self.language,
            "interrupt_mode": self.interrupt_mode,
            "metadata": self.metadata,
        }

        return d

    def to_json(self) -> str:
        """Serialise this kernelspec to a JSON object.

        Returns a string.
        """
        return json.dumps(self.to_dict())


_kernel_name_pat = re.compile(r"^[a-z0-9._\-]+$", re.IGNORECASE)


def _is_valid_kernel_name(name: str) -> t.Any:
    """Check that a kernel name is valid."""
    # quote is not unicode-safe on Python 2
    return _kernel_name_pat.match(name)


_kernel_name_description = (
    "Kernel names can only contain ASCII letters and numbers and these separators:"
    " - . _ (hyphen, period, and underscore)."
)


def _is_kernel_dir(path: str) -> bool:
    """Is ``path`` a kernel directory?"""
    return os.path.isdir(path) and os.path.isfile(pjoin(path, "kernel.json"))


def _list_kernels_in(dir: str | None) -> dict[str, str]:
    """Return a mapping of kernel names to resource directories from dir.

    If dir is None or does not exist, returns an empty dict.
    """
    if dir is None or not os.path.isdir(dir):
        return {}
    kernels = {}
    for f in os.listdir(dir):
        path = pjoin(dir, f)
        if not _is_kernel_dir(path):
            continue
        key = f.lower()
        if not _is_valid_kernel_name(key):
            warnings.warn(
                f"Invalid kernelspec directory name ({_kernel_name_description}): {path}",
                stacklevel=3,
            )
        kernels[key] = path
    return kernels


class NoSuchKernel(KeyError):  # noqa
    """An error raised when there is no kernel of a give name."""

    def __init__(self, name: str) -> None:
        """Initialize the error."""
        self.name = name

    def __str__(self) -> str:
        return f"No such kernel named {self.name}"


class KernelSpecManager(LoggingConfigurable):
    """A manager for kernel specs."""

    kernel_spec_class = Type(
        KernelSpec,
        config=True,
        help="""The kernel spec class.  This is configurable to allow
        subclassing of the KernelSpecManager for customized behavior.
        """,
    )

    ensure_native_kernel = Bool(
        True,
        config=True,
        help="""If there is no Python kernelspec registered and the IPython
        kernel is available, ensure it is added to the spec list.
        """,
    )

    data_dir = Unicode()

    def _data_dir_default(self) -> str:
        return jupyter_data_dir()

    user_kernel_dir = Unicode()

    def _user_kernel_dir_default(self) -> str:
        return pjoin(self.data_dir, "kernels")

    whitelist = Set(
        config=True,
        help="""Deprecated, use `KernelSpecManager.allowed_kernelspecs`
        """,
    )
    allowed_kernelspecs = Set(
        config=True,
        help="""List of allowed kernel names.

        By default, all installed kernels are allowed.
        """,
    )
    kernel_dirs: List[str] = List(
        help="List of kernel directories to search. Later ones take priority over earlier."
    )

    _deprecated_aliases = {
        "whitelist": ("allowed_kernelspecs", "7.0"),
    }

    _allow_insecure_kernelspec_params = False

    # Method copied from
    # https://github.com/jupyterhub/jupyterhub/blob/d1a85e53dccfc7b1dd81b0c1985d158cc6b61820/jupyterhub/auth.py#L143-L161
    @observe(*list(_deprecated_aliases))
    def _deprecated_trait(self, change: t.Any) -> None:
        """observer for deprecated traits"""
        old_attr = change.name
        new_attr, version = self._deprecated_aliases[old_attr]
        new_value = getattr(self, new_attr)
        if new_value != change.new:
            # only warn if different
            # protects backward-compatible config from warnings
            # if they set the same value under both names
            self.log.warning(
                f"{self.__class__.__name__}.{old_attr} is deprecated in jupyter_client "
                f"{version}, use {self.__class__.__name__}.{new_attr} instead"
            )
            setattr(self, new_attr, change.new)

    def _kernel_dirs_default(self) -> list[str]:
        dirs = jupyter_path("kernels")
        # At some point, we should stop adding .ipython/kernels to the path,
        # but the cost to keeping it is very small.
        try:
            # this should always be valid on IPython 3+
            from IPython.paths import get_ipython_dir

            dirs.append(os.path.join(get_ipython_dir(), "kernels"))
        except ModuleNotFoundError:
            pass
        return dirs

    def find_kernel_specs(self) -> dict[str, str]:
        """Returns a dict mapping kernel names to resource directories."""
        d = {}
        for kernel_dir in self.kernel_dirs:
            kernels = _list_kernels_in(kernel_dir)
            for kname, spec in kernels.items():
                if kname not in d:
                    self.log.debug("Found kernel %s in %s", kname, kernel_dir)
                    d[kname] = spec

        if self.ensure_native_kernel and NATIVE_KERNEL_NAME not in d:
            try:
                from ipykernel.kernelspec import RESOURCES

                self.log.debug(
                    "Native kernel (%s) available from %s",
                    NATIVE_KERNEL_NAME,
                    RESOURCES,
                )
                d[NATIVE_KERNEL_NAME] = RESOURCES
            except ImportError:
                self.log.warning("Native kernel (%s) is not available", NATIVE_KERNEL_NAME)

        if self.allowed_kernelspecs:
            # filter if there's an allow list
            d = {name: spec for name, spec in d.items() if name in self.allowed_kernelspecs}
        return d
        # TODO: Caching?

    def allow_insecure_kernelspec_params(self, allow_insecure_kernelspec_params):
        self._allow_insecure_kernelspec_params = allow_insecure_kernelspec_params

    def _check_parameterized_kernel(self, kspec: KernelSpec) -> KernelSpec:
        is_secure = self.check_kernel_is_secure(kspec=kspec)
        if is_secure == True:
            if kspec.metadata and isinstance(kspec.metadata, dict):
                kspec.metadata.update({"is_secure": True})
            else:
                kspec.metadata = {}
                kspec.metadata.update({"is_secure": True})
            return kspec  # a kernel spec is allowed
        else:
            if kspec.metadata and isinstance(kspec.metadata, dict):
                kspec.metadata.update({"is_secure": False})
            else:
                kspec.metadata = {}
                kspec.metadata.update({"is_secure": False})
            if self._allow_insecure_kernelspec_params == True:
                return kspec  # a kernel spec is allowed
            else:
                kspec_data = self.check_kernel_custom_all_default_values(kspec=kspec)

                if kspec_data["all_have_default"] == True:
                    return kspec_data["kspec"]  # a kernel spec is modyfied and is allowed
                else:
                    return None

    def check_kernel_is_secure(self, kspec):
        is_secure = False
        total_sum_kernel_variables = self.get_argv_env_kernel_variables(kspec=kspec)
        if (
            kspec.metadata
            and isinstance(kspec.metadata, dict)
            and "parameters" in kspec.metadata
            and isinstance(kspec.metadata["parameters"], dict)
            and "properties" in kspec.metadata["parameters"]
            and isinstance(kspec.metadata["parameters"]["properties"], dict)
        ):
            counter_secure_kernel_variables = self.get_count_secure_kernel_variables(
                obj=kspec.metadata["parameters"], counter_secure_kernel_variables=0
            )
            if total_sum_kernel_variables > 0:
                if counter_secure_kernel_variables == total_sum_kernel_variables:
                    is_secure = True
                else:
                    is_secure = False
            else:
                is_secure = False
        else:
            # check if there are kernel variables even metadata.parameters are empty
            if total_sum_kernel_variables > 0:
                is_secure = False
            else:
                is_secure = True
        return is_secure

    def get_argv_env_kernel_variables(self, kspec):
        total_sum_kernel_variables = 0
        env = None
        argv = None
        sum_argv_kernel_variables = 0
        sum_env_kernel_variables = 0
        if hasattr(kspec, "env"):
            env = kspec.env
            sum_env_kernel_variables = self.get_count_all_kernel_variables(parameters=env)
        if hasattr(kspec, "argv"):
            argv = kspec.argv
            sum_argv_kernel_variables = self.get_count_all_kernel_variables(parameters=argv)
        total_sum_kernel_variables = sum_env_kernel_variables + sum_argv_kernel_variables
        return total_sum_kernel_variables

    def get_count_secure_kernel_variables(self, obj, counter_secure_kernel_variables):
        is_secure = True
        if "properties" in obj:
            propetries = obj["properties"].items()
            if len(propetries) > 0:
                for property_key, property_value in propetries:
                    if (
                        property_value.get("type") == "string"
                        or property_value.get("type") == "null"
                    ):
                        if property_value.get("enum"):
                            counter_secure_kernel_variables = counter_secure_kernel_variables + 1
                        else:
                            is_secure = False
                    elif property_value.get("type") == "array":
                        print("Type of JSON Schema data is array and it is not supported now")
                        is_secure = False
                    elif property_value.get("enum"):
                        counter_secure_kernel_variables = counter_secure_kernel_variables + 1
                    elif property_value.get("type") == "object":
                        counter_secure_kernel_variables = self.get_count_secure_kernel_variables(
                            obj=obj, counter_secure_kernel_variables=counter_secure_kernel_variables
                        )

        if is_secure == False:
            counter_secure_kernel_variables = 0

        return counter_secure_kernel_variables

    def get_count_all_kernel_variables(self, parameters):
        sum = 0
        if isinstance(parameters, list):
            for argv_item in parameters:
                is_variable = self.has_variable(argv_item)
                if is_variable:
                    sum = sum + 1
        elif isinstance(parameters, dict):
            for env_key, env_item in parameters.items():
                is_variable = self.has_variable(env_item)
                if is_variable:
                    sum = sum + 1
        return sum

    def has_variable(self, string: str):
        pattern = re.compile(r"\{connection_file\}")
        match = pattern.match(string)
        if match is None:
            pattern = re.compile(r"\{([A-Za-z0-9_]+)\}")
            matches = pattern.findall(string)
            if len(matches) > 0:
                return True
            else:
                return False
        else:
            return False

    def check_kernel_custom_all_default_values(self, kspec):
        if (
            kspec.metadata
            and isinstance(kspec.metadata, dict)
            and "parameters" in kspec.metadata
            and isinstance(kspec.metadata["parameters"], dict)
            and "properties" in kspec.metadata["parameters"]
            and isinstance(kspec.metadata["parameters"]["properties"], dict)
        ):
            has_default = True
            propetries = kspec.metadata["parameters"]["properties"].items()

            new_kspec = {}
            for property_key, property_value in propetries:
                if "default" in property_value:
                    new_kspec = self.replaceByDefault(
                        kspec, property_key, property_value["default"]
                    )
                else:
                    has_default = False

            if has_default == False:
                result = {"kspec": kspec, "all_have_default": False}
            else:
                # check if there is anything after replacing
                total_sum_kernel_variables = self.get_argv_env_kernel_variables(kspec=new_kspec)

                if total_sum_kernel_variables > 0:
                    result = {"kspec": kspec, "all_have_default": False}
                else:
                    result = {"kspec": new_kspec, "all_have_default": True}
        else:
            result = {"kspec": kspec, "all_have_default": False}
        return result

    def replace_spec_parameter(self, variable, value, spec) -> str:
        regexp = r"\{" + variable + "\\}"
        pattern = re.compile(regexp)
        return pattern.sub(value, spec)

    def replaceByDefault(self, kspec, kernel_variable, default_value):
        new_env = {}
        new_argv = []
        if hasattr(kspec, "env"):
            tmp_env = kspec.env.copy()
            if "env" in tmp_env:
                env = tmp_env.env
                # check and replace env variables

                for env_key, env_item in env.items():
                    new_env_item = self.replace_spec_parameter(
                        kernel_variable, default_value, env_item
                    )
                    new_env[env_key] = new_env_item

                if len(new_env) > 0:
                    tmp_env.update(new_env)
                    kspec.env = tmp_env

        # check and replace argv parameters
        if hasattr(kspec, "argv") and kspec.argv is not None:
            argv = kspec.argv.copy()
            for argv_item in argv:
                new_argv_item = self.replace_spec_parameter(
                    kernel_variable, default_value, argv_item
                )
                new_argv.append(new_argv_item)

            if len(new_argv) > 0:
                argv = new_argv
                kspec.argv = new_argv
        return kspec

    def _get_kernel_spec_by_name(self, kernel_name: str, resource_dir: str) -> KernelSpec:
        """Returns a :class:`KernelSpec` instance for a given kernel_name
        and resource_dir.
        """
        kspec = None
        if kernel_name == NATIVE_KERNEL_NAME:
            try:
                from ipykernel.kernelspec import RESOURCES, get_kernel_dict
            except ImportError:
                # It should be impossible to reach this, but let's play it safe
                pass
            else:
                if resource_dir == RESOURCES:
                    kdict = get_kernel_dict()
                    kspec = self.kernel_spec_class(resource_dir=resource_dir, **kdict)
        if not kspec:
            kspec = self.kernel_spec_class.from_resource_dir(resource_dir)

        if not KPF.instance(parent=self.parent).is_provisioner_available(kspec):
            raise NoSuchKernel(kernel_name)

        kspec = self._check_parameterized_kernel(kspec)

        if kspec is not None:
            return kspec
        else:
            return None

    def _find_spec_directory(self, kernel_name: str) -> str | None:
        """Find the resource directory of a named kernel spec"""
        for kernel_dir in [kd for kd in self.kernel_dirs if os.path.isdir(kd)]:
            files = os.listdir(kernel_dir)
            for f in files:
                path = pjoin(kernel_dir, f)
                if f.lower() == kernel_name and _is_kernel_dir(path):
                    return path

        if kernel_name == NATIVE_KERNEL_NAME:
            try:
                from ipykernel.kernelspec import RESOURCES
            except ImportError:
                pass
            else:
                return RESOURCES
        return None

    def get_kernel_spec(self, kernel_name: str) -> KernelSpec:
        """Returns a :class:`KernelSpec` instance for the given kernel_name.

        Raises :exc:`NoSuchKernel` if the given kernel name is not found.
        """
        if not _is_valid_kernel_name(kernel_name):
            self.log.warning(
                f"Kernelspec name {kernel_name} is invalid: {_kernel_name_description}"
            )

        resource_dir = self._find_spec_directory(kernel_name.lower())
        if resource_dir is None:
            self.log.warning("Kernelspec name %s cannot be found!", kernel_name)
            raise NoSuchKernel(kernel_name)

        return self._get_kernel_spec_by_name(kernel_name, resource_dir)

    def get_all_specs(self) -> dict[str, t.Any]:
        """Returns a dict mapping kernel names to kernelspecs.

        Returns a dict of the form::

            {
              'kernel_name': {
                'resource_dir': '/path/to/kernel_name',
                'spec': {"the spec itself": ...}
              },
              ...
            }
        """
        d = self.find_kernel_specs()
        res = {}
        for kname, resource_dir in d.items():
            try:
                if self.__class__ is KernelSpecManager:
                    spec = self._get_kernel_spec_by_name(kname, resource_dir)
                else:
                    # avoid calling private methods in subclasses,
                    # which may have overridden find_kernel_specs
                    # and get_kernel_spec, but not the newer get_all_specs
                    spec = self.get_kernel_spec(kname)
                if spec != None:
                    res[kname] = {"resource_dir": resource_dir, "spec": spec.to_dict()}
            except NoSuchKernel:
                pass  # The appropriate warning has already been logged
            except Exception:
                self.log.warning("Error loading kernelspec %r", kname, exc_info=True)
        return res

    def remove_kernel_spec(self, name: str) -> str:
        """Remove a kernel spec directory by name.

        Returns the path that was deleted.
        """
        save_native = self.ensure_native_kernel
        try:
            self.ensure_native_kernel = False
            specs = self.find_kernel_specs()
        finally:
            self.ensure_native_kernel = save_native
        spec_dir = specs[name]
        self.log.debug("Removing %s", spec_dir)
        if os.path.islink(spec_dir):
            os.remove(spec_dir)
        else:
            shutil.rmtree(spec_dir)
        return spec_dir

    def _get_destination_dir(
        self, kernel_name: str, user: bool = False, prefix: str | None = None
    ) -> str:
        if user:
            return os.path.join(self.user_kernel_dir, kernel_name)
        elif prefix:
            return os.path.join(os.path.abspath(prefix), "share", "jupyter", "kernels", kernel_name)
        else:
            return os.path.join(SYSTEM_JUPYTER_PATH[0], "kernels", kernel_name)

    def install_kernel_spec(
        self,
        source_dir: str,
        kernel_name: str | None = None,
        user: bool = False,
        replace: bool | None = None,
        prefix: str | None = None,
    ) -> str:
        """Install a kernel spec by copying its directory.

        If ``kernel_name`` is not given, the basename of ``source_dir`` will
        be used.

        If ``user`` is False, it will attempt to install into the systemwide
        kernel registry. If the process does not have appropriate permissions,
        an :exc:`OSError` will be raised.

        If ``prefix`` is given, the kernelspec will be installed to
        PREFIX/share/jupyter/kernels/KERNEL_NAME. This can be sys.prefix
        for installation inside virtual or conda envs.
        """
        source_dir = source_dir.rstrip("/\\")
        if not kernel_name:
            kernel_name = os.path.basename(source_dir)
        kernel_name = kernel_name.lower()
        if not _is_valid_kernel_name(kernel_name):
            msg = f"Invalid kernel name {kernel_name!r}.  {_kernel_name_description}"
            raise ValueError(msg)

        if user and prefix:
            msg = "Can't specify both user and prefix. Please choose one or the other."
            raise ValueError(msg)

        if replace is not None:
            warnings.warn(
                "replace is ignored. Installing a kernelspec always replaces an existing "
                "installation",
                DeprecationWarning,
                stacklevel=2,
            )

        destination = self._get_destination_dir(kernel_name, user=user, prefix=prefix)
        self.log.debug("Installing kernelspec in %s", destination)

        kernel_dir = os.path.dirname(destination)
        if kernel_dir not in self.kernel_dirs:
            self.log.warning(
                "Installing to %s, which is not in %s. The kernelspec may not be found.",
                kernel_dir,
                self.kernel_dirs,
            )

        if os.path.isdir(destination):
            self.log.info("Removing existing kernelspec in %s", destination)
            shutil.rmtree(destination)

        shutil.copytree(source_dir, destination)
        self.log.info("Installed kernelspec %s in %s", kernel_name, destination)
        return destination

    def install_native_kernel_spec(self, user: bool = False) -> None:
        """DEPRECATED: Use ipykernel.kernelspec.install"""
        warnings.warn(
            "install_native_kernel_spec is deprecated. Use ipykernel.kernelspec import install.",
            stacklevel=2,
        )
        from ipykernel.kernelspec import install

        install(self, user=user)


def find_kernel_specs() -> dict[str, str]:
    """Returns a dict mapping kernel names to resource directories."""
    return KernelSpecManager().find_kernel_specs()


def get_kernel_spec(kernel_name: str) -> KernelSpec:
    """Returns a :class:`KernelSpec` instance for the given kernel_name.

    Raises KeyError if the given kernel name is not found.
    """
    return KernelSpecManager().get_kernel_spec(kernel_name)


def install_kernel_spec(
    source_dir: str,
    kernel_name: str | None = None,
    user: bool = False,
    replace: bool | None = False,
    prefix: str | None = None,
) -> str:
    """Install a kernel spec in a given directory."""
    return KernelSpecManager().install_kernel_spec(source_dir, kernel_name, user, replace, prefix)


install_kernel_spec.__doc__ = KernelSpecManager.install_kernel_spec.__doc__


def install_native_kernel_spec(user: bool = False) -> None:
    """Install the native kernel spec."""
    KernelSpecManager().install_native_kernel_spec(user=user)


install_native_kernel_spec.__doc__ = KernelSpecManager.install_native_kernel_spec.__doc__
