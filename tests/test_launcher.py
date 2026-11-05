"""Tests for launching kernel processes."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import sys
from types import ModuleType, SimpleNamespace

import pytest

from jupyter_client import launcher


class _FakeStdin:
    def close(self) -> None:
        pass


class _FakePopen:
    def __init__(self, cmd: list[str], **kwargs: object) -> None:
        self.cmd = cmd
        self.kwargs = kwargs
        self.stdin = _FakeStdin()


class _FailingPopen:
    def __init__(self, cmd: list[str], **kwargs: object) -> None:
        msg = "failed to spawn"
        raise OSError(msg)


def _install_fake_winapi(monkeypatch: pytest.MonkeyPatch, closed: list[int]) -> None:
    """Install a fake _winapi module so the win32 branch runs on any platform."""
    fake = ModuleType("_winapi")
    fake.CREATE_NEW_PROCESS_GROUP = 0x00000200  # type: ignore[attr-defined]
    fake.DUPLICATE_SAME_ACCESS = 0x00000002  # type: ignore[attr-defined]
    fake.GetCurrentProcess = lambda: 4242  # type: ignore[attr-defined]
    fake.DuplicateHandle = lambda *args: 7777  # type: ignore[attr-defined]
    fake.CloseHandle = closed.append  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "_winapi", fake)


def test_win32_launch_closes_parent_handle(monkeypatch: pytest.MonkeyPatch) -> None:
    """The parent-handle duplicate is closed once the child has inherited it."""
    closed: list[int] = []
    _install_fake_winapi(monkeypatch, closed)
    monkeypatch.setattr(
        launcher, "sys", SimpleNamespace(platform="win32", executable=sys.executable)
    )
    monkeypatch.setattr(launcher, "Popen", _FakePopen)
    monkeypatch.setattr("jupyter_client.win_interrupt.create_interrupt_event", lambda: 5555)

    proc = launcher.launch_kernel(["fake-kernel"])

    assert closed == [7777]
    assert proc.win32_interrupt_event == 5555
    assert proc.kwargs["env"]["JPY_PARENT_PID"] == "7777"


def test_win32_launch_closes_handles_on_popen_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed launch must not leak either handle."""
    closed: list[int] = []
    _install_fake_winapi(monkeypatch, closed)
    monkeypatch.setattr(
        launcher, "sys", SimpleNamespace(platform="win32", executable=sys.executable)
    )
    monkeypatch.setattr(launcher, "Popen", _FailingPopen)
    monkeypatch.setattr("jupyter_client.win_interrupt.create_interrupt_event", lambda: 5555)
    monkeypatch.setattr("jupyter_client.win_interrupt.close_interrupt_event", closed.append)

    with pytest.raises(OSError, match="failed to spawn"):
        launcher.launch_kernel(["fake-kernel"])

    assert closed == [7777, 5555]
