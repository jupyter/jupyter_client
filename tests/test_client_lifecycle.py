"""Tests for KernelClient garbage-collection lifecycle."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from unittest.mock import MagicMock

import pytest
import traitlets.traitlets

from jupyter_client.client import KernelClient


def test_kernel_client_del_during_interpreter_shutdown(monkeypatch):
    """__del__ must not trigger traitlets defaults when module globals are cleared."""
    kc = KernelClient()
    ctx = kc.context
    kc._trait_values.pop("log", None)
    monkeypatch.setattr(traitlets.traitlets, "Bunch", None)

    try:
        kc.__del__()
        assert ctx.closed
    finally:
        if not ctx.closed:
            ctx.destroy(linger=0)


@pytest.mark.parametrize("clear_created_context", [False, True])
def test_kernel_client_del_missing_trait_values_during_shutdown(monkeypatch, clear_created_context):
    """__del__ must not raise TypeError if traitlets globals are cleared before GC."""
    kc = KernelClient()
    if clear_created_context:
        kc._trait_values.pop("_created_context", None)
    else:
        kc._trait_values["_created_context"] = True
    monkeypatch.setattr(traitlets.traitlets, "Bunch", None)

    kc.__del__()
    assert "context" not in kc._trait_values


def test_kernel_client_del_does_not_lazily_create_context():
    """__del__ must not instantiate a new zmq.Context if none was created."""
    kc = KernelClient()
    kc._created_context = True

    kc.__del__()

    assert "context" not in kc._trait_values


def test_kernel_client_del_destroys_owned_context_when_channels_stopped():
    """__del__ destroys an owned context when no channels are running."""
    kc = KernelClient()
    ctx = kc.context
    assert not ctx.closed

    kc.__del__()

    assert ctx.closed


def test_kernel_client_del_keeps_context_while_channels_running():
    """__del__ does not destroy the context while channels are still running."""
    kc = KernelClient()
    ctx = kc.context
    channel = MagicMock()
    channel.is_alive.return_value = True
    kc._trait_values["_shell_channel"] = channel

    try:
        kc.__del__()
        assert not ctx.closed
    finally:
        ctx.destroy(linger=0)


def test_kernel_client_del_uninitialized_instance():
    """__del__ handles instances without _trait_values."""
    kc = KernelClient.__new__(KernelClient)
    del kc._trait_values
    kc.__del__()
