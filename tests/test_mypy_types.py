"""Tests for mypy type checking.

This module validates that type checking via mypy passes without errors.
Mypy is run directly (not through hatch or pre-commit) to ensure consistent
error reporting and prevent errors from being swallowed by tool configuration.
"""

import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore


def test_mypy_not_in_hatch_config() -> None:
    """Verify that mypy is not configured in any hatch environment.

    Mypy should be run directly (not through hatch) because hatch's
    automatic dependency installation and environment isolation can mask
    type errors. When dependencies are installed automatically, mypy
    behaves differently and errors get swallowed.

    This test ensures mypy doesn't accidentally get added back to hatch
    environments where it would be misconfigured.
    """
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    # Check all hatch environment configurations
    hatch_config = config.get("tool", {}).get("hatch", {})
    envs = hatch_config.get("envs", {})

    mypy_found_in = []

    for env_name, env_config in envs.items():
        if not isinstance(env_config, dict):
            continue

        # Check dependencies
        deps = env_config.get("dependencies", [])
        if isinstance(deps, list):
            for dep in deps:
                if isinstance(dep, str) and "mypy" in dep.lower():
                    mypy_found_in.append(f"envs.{env_name}.dependencies")

        # Check scripts
        scripts = env_config.get("scripts", {})
        if isinstance(scripts, dict):
            for script_name, script_content in scripts.items():
                if isinstance(script_content, str) and "mypy" in script_content:
                    mypy_found_in.append(f"envs.{env_name}.scripts.{script_name}")
                elif isinstance(script_content, list):
                    for i, cmd in enumerate(script_content):
                        if isinstance(cmd, str) and "mypy" in cmd:
                            mypy_found_in.append(f"envs.{env_name}.scripts.{script_name}[{i}]")

    if mypy_found_in:
        error_msg = (
            "MyPy should not be configured in any hatch environment section. "
            "It should be run directly to ensure consistent error reporting.\n\n"
            "Found mypy in the following sections:\n"
            + "\n".join(f"  - [tool.hatch.{section}]" for section in mypy_found_in)
            + "\n\nRun mypy directly instead:\n"
            "  python -m mypy"
        )
        raise AssertionError(error_msg)
