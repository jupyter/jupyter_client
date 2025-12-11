"""Tests for pre-commit configuration.

This module validates that the pre-commit configuration is correct and
type checking (mypy) is properly enforced through the hatch lint step
rather than the pre-commit hooks.
"""

import sys
from pathlib import Path

# Import yaml, handling potential missing module gracefully
try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

import pytest


def test_mypy_not_in_precommit() -> None:
    """Verify that mypy is not in the pre-commit configuration.

    Mypy should be run through `hatch lint` instead of pre-commit because:
    1. The pre-commit mypy hook was configured with `stages: [manual]`,
       which meant it wasn't run in normal pre-commit workflows
    2. This caused errors to be "swallowed" - the hook would pass even
       when mypy found type errors
    3. Moving mypy to `hatch lint` ensures type checking is consistently
       enforced as part of the lint process

    The typing checks are available separately via `hatch run typing:test`
    if needed for manual type checking with pre-commit infrastructure.
    """
    if yaml is None:
        pytest.skip("PyYAML not available")

    config_path = Path(__file__).parent.parent / ".pre-commit-config.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    repos = config.get("repos", [])

    # Check that mypy is not in any pre-commit repo
    mypy_found = False
    for repo in repos:
        if "mypy" in repo.get("repo", ""):
            mypy_found = True
            break

        # Also check if any hook has id: mypy
        for hook in repo.get("hooks", []):
            if hook.get("id") == "mypy":
                mypy_found = True
                break

    assert not mypy_found, (
        "mypy should not be in .pre-commit-config.yaml. "
        "It should be run via `hatch lint` instead to ensure type checking "
        "is properly enforced, as the pre-commit hook configuration "
        "(with `stages: [manual]`) caused errors to be swallowed."
    )
