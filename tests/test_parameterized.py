"""Tests for ParameterizedKernelSpec"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import copy

import pytest

from jupyter_client.kernelspec import KernelSpec
from jupyter_client.parameterized import ParameterizedKernelSpec as P


def make_spec(argv=None, env=None, metadata=None):
    """Build a lightweight KernelSpec-like object."""
    spec = KernelSpec(
        resource_dir="test",
        **{
            "display_name": "test_kernel",
            "language": "python",
        },
    )
    spec.argv = argv or []
    spec.env = env or {}
    spec.metadata = metadata or {}
    return spec


def test_get_defaults_returns_declared_defaults():
    spec = make_spec(
        metadata={
            "parameters": {
                "properties": {
                    "host": {"type": "string", "default": "localhost"},
                    "port": {"type": "integer", "default": 8888},
                    "token": {"type": "string"},
                }
            }
        }
    )

    assert P.get_default_custom_kernel_specs_value(spec) == {
        "host": "localhost",
        "port": 8888,
    }


def test_get_defaults_returns_empty_when_no_properties():
    assert P.get_default_custom_kernel_specs_value(make_spec()) == {}


def test_get_defaults_ignores_non_dict_definitions():
    spec = make_spec(
        metadata={
            "parameters": {
                "properties": {
                    "host": "invalid",
                    "port": {"default": 8888},
                }
            }
        }
    )

    assert P.get_default_custom_kernel_specs_value(spec) == {"port": 8888}


@pytest.mark.parametrize(
    "value, expected",
    [
        ("python", set()),
        ("--host={host}", {"host"}),
        ("{host} {port}", {"host", "port"}),
        ("{host} {host}", {"host"}),
        ("{connection_file}", set()),
        ("{host-name}", set()),
        (None, set()),
        (123, set()),
    ],
)
def test_find_parameters(value, expected):
    assert P.find_parameters(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("--host={host}", True),
        ("{connection_file}", False),
        ("plain text", False),
        (None, False),
    ],
)
def test_has_custom_parameter(value, expected):
    assert P.has_custom_parameter(value) is expected


def test_counts_unique_parameters_per_argument_and_env_value():
    spec = make_spec(
        argv=["python", "--host={host}-{host}", "--port={port}"],
        env={"HOST": "{host}", "TOKEN": "{token}"},
    )

    assert P.get_argv_env_kernel_variables(spec) == 4


def test_count_is_zero_when_no_custom_parameters():
    spec = make_spec(argv=["python", "{connection_file}"], env={})

    assert P.get_argv_env_kernel_variables(spec) == 0


def test_substitute_resolved_parameters_only():
    assert (
        P.substitute_parameters(
            "--host={host}, --port={port}",
            {"host": "localhost"},
        )
        == "--host=localhost, --port={port}"
    )


def test_substitute_converts_values_to_strings():
    assert P.substitute_parameters("{port}", {"port": 8888}) == "8888"


def test_format_kernel_cmd():
    assert P.format_kernel_cmd(
        ["python", "--host={host}", "--port={port}"],
        {"host": "localhost", "port": 8888},
    ) == ["python", "--host=localhost", "--port=8888"]


def test_format_kernel_env():
    assert P.format_kernel_env(
        {"HOST": "{host}", "PORT": "{port}"},
        {"host": "localhost", "port": 8888},
    ) == {"HOST": "localhost", "PORT": "8888"}


def test_parameter_properties_returns_properties():
    spec = make_spec(metadata={"parameters": {"properties": {"host": {"type": "string"}}}})

    assert P._parameter_properties(spec) == {"host": {"type": "string"}}


def test_parameter_properties_handles_invalid_properties():
    spec = make_spec(metadata={"parameters": {"properties": ["host"]}})

    assert P._parameter_properties(spec) == {}


def test_parameter_properties_handles_missing_metadata():
    spec = make_spec(metadata={})

    assert P._parameter_properties(spec) == {}


def test_replace_by_default_updates_argv_and_env():
    spec = make_spec(
        argv=["python", "--host={host}", "--port={port}"],
        env={"HOST": "{host}", "PORT": "{port}"},
    )
    original_argv = copy.deepcopy(spec.argv)
    original_env = copy.deepcopy(spec.env)

    result = P.replace_by_default(spec, "host", "localhost")

    assert result.argv == ["python", "--host=localhost", "--port={port}"]
    assert result.env == {"HOST": "localhost", "PORT": "{port}"}
    assert spec.argv == original_argv
    assert spec.env == original_env
    assert result is not spec


def test_count_secure_string_enum():
    obj = {
        "properties": {
            "host": {
                "type": "string",
                "enum": ["localhost", "remote"],
            }
        }
    }

    assert P.get_count_secure_kernel_variables(obj) == 1


def test_count_secure_null_enum():
    obj = {"properties": {"token": {"type": "null", "enum": [None]}}}

    assert P.get_count_secure_kernel_variables(obj) == 1


def test_unrestricted_string_is_not_secure():
    obj = {"properties": {"host": {"type": "string"}}}

    assert P.get_count_secure_kernel_variables(obj) == 0


def test_array_property_is_not_secure():
    obj = {"properties": {"args": {"type": "array", "enum": [["a", "b"]]}}}

    assert P.get_count_secure_kernel_variables(obj) == 0


def test_empty_properties_return_zero():
    assert P.get_count_secure_kernel_variables({"properties": {}}) == 0


def test_kernel_without_parameters_and_placeholders_is_secure():
    spec = make_spec(argv=["python"], metadata={})

    assert P.check_kernel_is_secure(spec) is True


def test_kernel_without_parameter_metadata_is_insecure_with_placeholder():
    spec = make_spec(
        argv=["python", "--host={host}"],
        metadata={},
    )

    assert P.check_kernel_is_secure(spec) is False


def test_kernel_with_matching_enum_parameter_is_secure():
    spec = make_spec(
        argv=["python", "--host={host}"],
        metadata={
            "parameters": {
                "properties": {
                    "host": {
                        "type": "string",
                        "enum": ["localhost", "remote"],
                    }
                }
            }
        },
    )

    assert P.check_kernel_is_secure(spec) is True


def test_kernel_with_unrestricted_string_parameter_is_insecure():
    spec = make_spec(
        argv=["python", "--host={host}"],
        metadata={"parameters": {"properties": {"host": {"type": "string"}}}},
    )

    assert P.check_kernel_is_secure(spec) is False


def test_kernel_with_metadata_but_no_placeholders_is_insecure():
    spec = make_spec(
        argv=["python"],
        metadata={
            "parameters": {
                "properties": {
                    "host": {
                        "type": "string",
                        "enum": ["localhost"],
                    }
                }
            }
        },
    )

    assert P.check_kernel_is_secure(spec) is False


def test_all_defaults_resolve_all_placeholders():
    spec = make_spec(
        argv=["python", "--host={host}"],
        env={"HOST": "{host}"},
        metadata={
            "parameters": {
                "properties": {
                    "host": {
                        "type": "string",
                        "default": "localhost",
                    }
                }
            }
        },
    )

    result = P.check_kernel_custom_all_default_values(spec)

    assert result["all_have_default"] is True
    assert result["kspec"].argv == ["python", "--host=localhost"]
    assert result["kspec"].env == {"HOST": "localhost"}


def test_missing_default_makes_all_defaults_false():
    spec = make_spec(
        argv=["python", "--host={host}"],
        metadata={"parameters": {"properties": {"host": {"type": "string"}}}},
    )

    result = P.check_kernel_custom_all_default_values(spec)

    assert result["all_have_default"] is False


def test_no_parameter_properties_returns_false():
    spec = make_spec(argv=["python"], metadata={})

    result = P.check_kernel_custom_all_default_values(spec)

    assert result["all_have_default"] is False
    assert result["kspec"] is spec


def test_secure_kernel_is_returned_with_security_metadata():
    spec = make_spec(argv=["python"], metadata={})

    result = P.check_parameterized_kernel(spec)

    assert result is not None
    assert result.metadata["is_secure"] is True


def test_insecure_kernel_is_rejected_without_defaults():
    spec = make_spec(
        argv=["python", "--host={host}"],
        metadata={"parameters": {"properties": {"host": {"type": "string"}}}},
    )

    sanitized_spec = P.check_parameterized_kernel(spec)
    assert sanitized_spec is not None
    assert "--host={host}" not in sanitized_spec.argv
    assert sanitized_spec.argv == ["python"]
    assert sanitized_spec.metadata.get("is_secure") is False


def test_allow_insecure_kernel_returns_spec():
    spec = make_spec(
        argv=["python", "--host={host}"],
        metadata={"parameters": {"properties": {"host": {"type": "string"}}}},
    )

    result = P.check_parameterized_kernel(spec, allow_insecure_kernelspec_params=True)

    assert result is not None
    assert result.metadata["is_secure"] is False


def test_insecure_kernel_with_all_defaults_uses_fallback():
    spec = make_spec(
        argv=["python", "--host={host}"],
        metadata={
            "parameters": {
                "properties": {
                    "host": {
                        "type": "string",
                        "default": "localhost",
                    }
                }
            }
        },
    )

    result = P.check_parameterized_kernel(spec)

    assert result is not None
    assert result.argv == ["python", "--host=localhost"]
    assert result.metadata["is_secure"] is False


def test_custom_values_override_defaults():
    result = P.get_custom_kernel_spec_value(
        {"custom_kernel_specs": {"host": "remote"}},
        {"host": "localhost", "port": 8888},
    )

    assert result == {"host": "remote", "port": 8888}


def test_defaults_used_when_custom_values_are_absent():
    assert P.get_custom_kernel_spec_value({}, {"host": "localhost"}) == {"host": "localhost"}


def test_invalid_custom_values_type_uses_defaults():
    assert P.get_custom_kernel_spec_value(
        {"custom_kernel_specs": ["invalid"]},
        {"host": "localhost"},
    ) == {"host": "localhost"}


def test_no_custom_values_or_defaults_returns_empty_dict():
    assert P.get_custom_kernel_spec_value({}, {}) == {}


def test_clear_list_removes_empty_and_unresolved_items():
    assert P.clear_custom_kernel_parameters(["python", "", "--host={host}", "--debug"]) == [
        "python",
        "--debug",
    ]


def test_clear_list_preserves_original_if_result_empty():
    items = ["{host}", ""]

    assert P.clear_custom_kernel_parameters(items) == items


def test_clear_dict_removes_empty_and_unresolved_values():
    assert P.clear_custom_kernel_parameters(
        {
            "HOST": "localhost",
            "PORT": "{port}",
            "EMPTY": "",
        }
    ) == {"HOST": "localhost"}


def test_clear_dict_preserves_original_if_result_empty():
    values = {"HOST": "{host}", "EMPTY": ""}

    assert P.clear_custom_kernel_parameters(values) == values


@pytest.mark.parametrize(
    "value, expected",
    [
        ("", ""),
        ("{host}", ""),
        ("localhost", "localhost"),
        (123, 123),
        (None, None),
    ],
)
def test_clear_scalar_values(value, expected):
    assert P.clear_custom_kernel_parameters(value) == expected


def test_update_custom_env_parameters_uses_user_values_and_defaults():
    env = {
        "HOST": "{host}",
        "PORT": "{port}",
        "STATIC": "unchanged",
        "OPTIONAL": "{missing}",
    }

    result = P.update_custom_env_parameters(
        {"custom_kernel_specs": {"host": "remote"}},
        {"host": "localhost", "port": 8888},
        env,
    )

    assert result == {
        "HOST": "remote",
        "PORT": "8888",
        "STATIC": "unchanged",
    }


def test_update_custom_env_parameters_with_no_values():
    result = P.update_custom_env_parameters({}, {}, {"STATIC": "unchanged", "HOST": "{host}"})

    assert result == {"STATIC": "unchanged"}


def test_update_custom_arg_parameters_uses_defaults_and_custom_values():
    spec = make_spec(
        argv=[],
        metadata={
            "parameters": {
                "properties": {
                    "host": {
                        "type": "string",
                        "default": "localhost",
                    },
                    "port": {
                        "type": "integer",
                        "default": 8888,
                    },
                }
            }
        },
    )

    result = P.update_custom_arg_parameters(
        spec,
        ["python", "--host={host}", "--port={port}", "--token={token}"],
        {"custom_kernel_specs": {"host": "remote"}},
    )

    assert result == ["python", "--host=remote", "--port=8888"]


def test_update_custom_arg_parameters_with_no_parameters():
    spec = make_spec(argv=["python"], metadata={})

    result = P.update_custom_arg_parameters(spec, ["python", "--version"], {})

    assert result == ["python", "--version"]
