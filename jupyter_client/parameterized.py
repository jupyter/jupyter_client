# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import copy
import re
import typing as t

from traitlets.log import get_logger

from . import kernelspec

_PLACEHOLDER = re.compile(r"\{([A-Za-z0-9_]+)\}")
_CONNECTION_FILE = "connection_file"

KernelParamType = t.Union[t.List[str], t.Dict[str, str], str]


class ParameterizedKernelSpec:
    """Shared helpers for parameterized kernelspecs."""

    @classmethod
    def get_default_custom_kernel_specs_value(
        cls, kspec: kernelspec.KernelSpec
    ) -> dict[str, t.Any]:
        """Get default values of custom kernel specs."""

        properties = cls._parameter_properties(kspec)
        if not properties:
            return {}

        return {
            name: definition["default"]
            for name, definition in properties.items()
            if isinstance(definition, dict) and "default" in definition
        }

    @staticmethod
    def find_parameters(value: t.Any) -> set[str]:
        """Find custom kernel variables."""
        if not isinstance(value, str):
            return set()

        return {name for name in _PLACEHOLDER.findall(value) if name != _CONNECTION_FILE}

    @classmethod
    def has_custom_parameter(cls, value: t.Any) -> bool:
        return bool(cls.find_parameters(value))

    @classmethod
    def get_argv_env_kernel_variables(cls, kspec: kernelspec.KernelSpec) -> int:
        """Count total custom kernel variables for args and envs together."""
        total = 0

        for value in getattr(kspec, "argv", None) or []:
            total += len(cls.find_parameters(value))

        for value in (getattr(kspec, "env", None) or {}).values():
            total += len(cls.find_parameters(value))

        return total

    @staticmethod
    def substitute_parameters(
        value: t.Any,
        values: dict[str, t.Any],
    ) -> str:
        """Substitute only values that were explicitly resolved."""
        return _PLACEHOLDER.sub(
            lambda match: (
                str(values[match.group(1)]) if match.group(1) in values else match.group(0)
            ),
            value,
        )

    @classmethod
    def format_kernel_cmd(
        cls,
        cmd: t.List[t.Any],
        values: dict[str, t.Any],
    ) -> list[str]:
        """Replace arg custom kernel variables by values."""
        return [cls.substitute_parameters(arg, values) for arg in cmd]

    @classmethod
    def format_kernel_env(
        cls,
        env: t.Dict[str, t.Any],
        values: dict[str, t.Any],
    ) -> dict[str, str]:
        """Replace env custom kernel variables by values."""
        return {key: cls.substitute_parameters(value, values) for key, value in env.items()}

    @staticmethod
    def _parameter_properties(kspec: kernelspec.KernelSpec) -> dict[str, t.Any]:
        """Return properties part of kernel metadata."""

        metadata = getattr(kspec, "metadata", None) or {}
        parameters = metadata.get("parameters", {})
        properties = parameters.get("properties", {})
        return properties if isinstance(properties, dict) else {}

    @classmethod
    def get_count_secure_kernel_variables(
        cls, obj: dict[str, t.Any], counter_secure_kernel_variables: int = 0
    ) -> int:
        """Count secured custom kernel variables recursively."""
        properties = obj.get("properties")
        if not isinstance(properties, dict):
            return counter_secure_kernel_variables  #

        for _property_key, property_value in properties.items():
            if not isinstance(property_value, dict):
                continue

            prop_type = property_value.get("type")

            if prop_type == "array":
                return 0

            if prop_type in ("string", "null"):
                if property_value.get("enum"):
                    counter_secure_kernel_variables += 1
                else:
                    return 0

            elif prop_type == "object":
                counter_secure_kernel_variables = cls.get_count_secure_kernel_variables(
                    obj=property_value,
                    counter_secure_kernel_variables=counter_secure_kernel_variables,
                )
                if counter_secure_kernel_variables == 0:
                    return 0

            elif property_value.get("enum"):
                counter_secure_kernel_variables += 1

        return counter_secure_kernel_variables

    @classmethod
    def get_kernel_variable_names(cls, kspec: kernelspec.KernelSpec) -> set[str]:
        """Return the set of variables referenced in argv and env."""

        variables = set()

        def extract(value: t.Any) -> None:
            if isinstance(value, str):
                variables.update(cls.find_parameters(value))

            elif isinstance(value, list):
                for item in value:
                    extract(item)

            elif isinstance(value, dict):
                for item in value.values():
                    extract(item)

        extract(kspec.argv)
        extract(kspec.env or {})

        return variables

    @classmethod
    def check_kernel_is_secure(cls, kspec: kernelspec.KernelSpec) -> bool:
        """Return True if all custom kernel variables are secure."""

        properties = cls._parameter_properties(kspec)

        total_sum_kernel_variables = cls.get_argv_env_kernel_variables(kspec)

        if not properties:
            return total_sum_kernel_variables == 0

        kernel_variables = cls.get_kernel_variable_names(kspec)

        secure_parameters = set(properties.keys())

        unresolved_parameters = kernel_variables - secure_parameters

        counter_secure_kernel_variables = cls.get_count_secure_kernel_variables(
            obj=kspec.metadata["parameters"], counter_secure_kernel_variables=0
        )

        if counter_secure_kernel_variables == 0 or unresolved_parameters:
            get_logger().warning(
                "The kernelspec is unsecure. Secured kernel variables: %s | Unresolved parameters: %s",
                counter_secure_kernel_variables,
                unresolved_parameters,
            )
            return False
        elif (
            total_sum_kernel_variables > 0
            and counter_secure_kernel_variables == total_sum_kernel_variables
        ):
            return True
        else:
            get_logger().warning(
                "The kernelspec is unsecure. The sum of all kernel variables and number of secured kernel variables are not equal. Total kernel variables: %s | Secured kernel variables: %s",
                total_sum_kernel_variables,
                counter_secure_kernel_variables,
            )

            return False

    @classmethod
    def replace_by_default(
        cls,
        kspec: kernelspec.KernelSpec,
        kernel_variable: str,
        default_value: t.Any,
    ) -> t.Any:
        """Replaces args and env by default values."""
        result = copy.deepcopy(kspec)

        result.argv = cls.format_kernel_cmd(
            list(result.argv or []),
            {kernel_variable: default_value},
        )

        result.env = cls.format_kernel_env(
            dict(getattr(result, "env", None) or {}),
            {kernel_variable: default_value},
        )

        return result

    @classmethod
    def check_kernel_custom_all_default_values(
        cls, kspec: kernelspec.KernelSpec
    ) -> dict[str, t.Any]:
        """Check whether there are default values for all custom kernel variables."""
        assert kspec is not None
        properties = cls._parameter_properties(kspec)
        if properties:
            has_default = True

            new_kspec = copy.deepcopy(kspec)
            for property_key, property_value in properties.items():
                if isinstance(property_value, dict) and "default" in property_value:
                    new_kspec = cls.replace_by_default(
                        new_kspec, property_key, property_value["default"]
                    )
                else:
                    has_default = False

            if has_default is False:
                result = {"kspec": new_kspec, "all_have_default": False}
            else:
                # check if there is anything after replacing
                total_sum_kernel_variables = cls.get_argv_env_kernel_variables(kspec=new_kspec)

                if total_sum_kernel_variables > 0:
                    result = {"kspec": new_kspec, "all_have_default": False}
                else:
                    result = {"kspec": new_kspec, "all_have_default": True}
        else:
            result = {"kspec": kspec, "all_have_default": False}
        return result

    @classmethod
    def check_parameterized_kernel(
        cls,
        kspec: kernelspec.KernelSpec,
        allow_insecure_kernelspec_params: bool = False,
    ) -> kernelspec.KernelSpec:
        """Apply the security policy and default-value fallback."""
        # check whether there are custom kernel spec variables and if so whether they have configuration and its configuration is safe
        is_secure = cls.check_kernel_is_secure(kspec)

        result = copy.deepcopy(kspec)
        metadata = dict(getattr(result, "metadata", None) or {})
        metadata["is_secure"] = is_secure
        result.metadata = metadata

        # Case 1: Clean kernel or unsafe parameters explicitly permitted
        if is_secure or allow_insecure_kernelspec_params:
            return result

        # Case 2: Insecure parameters found -> Fall back to factory defaults
        fallback = cls.check_kernel_custom_all_default_values(result)
        fallback_spec = fallback["kspec"]
        fallback_metadata = dict(getattr(fallback_spec, "metadata", None) or {})
        fallback_metadata["is_secure"] = False
        fallback_spec.metadata = fallback_metadata

        if fallback["all_have_default"]:
            return fallback_spec
        else:
            # Case 3: Broken/incomplete defaults -> Emergency purge remaining brackets
            if hasattr(fallback_spec, "argv") and fallback_spec.argv:
                fallback_spec.argv = cls.clear_custom_kernel_parameters(fallback_spec.argv)
            if hasattr(fallback_spec, "env") and fallback_spec.env:
                fallback_spec.env = cls.clear_custom_kernel_parameters(fallback_spec.env)
            return fallback_spec

    @classmethod
    def get_custom_kernel_spec_value(
        cls, launch_args: t.Dict[str, t.Any], custom_kernel_default_value: dict[str, t.Any]
    ) -> dict[str, t.Any]:
        """Get value for a custom kernel variable. In case it is not present it takes its default value."""
        custom_kernel_dict = {}
        if "custom_kernel_specs" in launch_args:
            custom_kernel_specs = launch_args["custom_kernel_specs"].copy()
            custom_kernel_dict = (
                custom_kernel_specs.copy() if isinstance(custom_kernel_specs, dict) else {}
            )

            # check is custom kernel variables are full if not then we should take default ones
            if custom_kernel_default_value:
                for key, value in custom_kernel_default_value.items():
                    if key not in custom_kernel_dict:
                        custom_kernel_dict[key] = value
        elif custom_kernel_default_value:
            # if not but default values are present into a kernel.json file then we have to take them
            custom_kernel_dict = custom_kernel_default_value.copy()
        return custom_kernel_dict

    @classmethod
    def clear_custom_kernel_parameters(cls, kernel_parameters: t.Any) -> KernelParamType:
        """Safely removes unresolved custom kernel variables.Logs a warning when parameters are dropped."""

        if isinstance(kernel_parameters, list):
            clean_parameters = []
            dropped_parameters = []

            for item in kernel_parameters:
                if item == "" or cls.has_custom_parameter(item):
                    dropped_parameters.append(item)
                else:
                    clean_parameters.append(item)

            if dropped_parameters:
                get_logger().warning(
                    "Dropping unresolved custom kernel parameters: %s",
                    dropped_parameters,
                )

            return clean_parameters if clean_parameters else kernel_parameters

        elif isinstance(kernel_parameters, dict):
            clean_parameters_dict = {}
            dropped_parameters = []

            for key, value in kernel_parameters.items():
                if value == "" or cls.has_custom_parameter(value):
                    dropped_parameters.append(value)
                else:
                    clean_parameters_dict[key] = value

            if dropped_parameters:
                get_logger().warning(
                    "Dropping unresolved custom kernel parameters: %s",
                    dropped_parameters,
                )

            return clean_parameters_dict if clean_parameters_dict else kernel_parameters

        elif isinstance(kernel_parameters, str):
            if kernel_parameters == "" or cls.has_custom_parameter(kernel_parameters):
                get_logger().warning(
                    "Dropping unresolved custom kernel parameter: %s",
                    kernel_parameters,
                )
                return ""

            return kernel_parameters

        return kernel_parameters

    @classmethod
    def update_custom_env_parameters(
        cls,
        launch_args: t.Dict[str, t.Any],
        custom_kernel_default_value: dict[str, t.Any],
        env: t.Dict[str, str],
    ) -> KernelParamType:
        """Replace custom kernel variables in env."""
        custom_kernel_dict = cls.get_custom_kernel_spec_value(
            launch_args, custom_kernel_default_value
        )
        newEnv = cls.format_kernel_env(env, custom_kernel_dict)
        return cls.clear_custom_kernel_parameters(newEnv)

    @classmethod
    def update_custom_arg_parameters(
        cls, kpecs: kernelspec.KernelSpec, cmd: t.List[t.Any], kwargs: t.Dict[str, t.Any]
    ) -> KernelParamType:
        """Replace custom kernel variables in args."""
        custom_kernel_default_value = cls.get_default_custom_kernel_specs_value(kpecs)

        custom_kernel_dict = cls.get_custom_kernel_spec_value(kwargs, custom_kernel_default_value)
        newArgs = cls.format_kernel_cmd(cmd, custom_kernel_dict)
        return cls.clear_custom_kernel_parameters(newArgs)
