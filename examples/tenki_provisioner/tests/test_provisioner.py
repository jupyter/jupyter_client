"""Unit tests for the Tenki kernel provisioner (SDK fully mocked).

The live, end-to-end path (a real kernel in a real microVM) is exercised
separately; these tests pin down the provisioner's control logic and the
loopback socket proxy without needing Tenki credentials.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import threading

import pytest
from jupyter_client.kernelspec import KernelSpec
from traitlets.config import LoggingConfigurable

from tenki_provisioner import TenkiProvisioner
from tenki_provisioner._proxy import IpcSocketProxy

# --------------------------------------------------------------------------- fakes


class FakeKernelManager(LoggingConfigurable):
    """Minimal stand-in for a ConnectionFileMixin/KernelManager."""

    def __init__(self, conn_path: str, **kw):
        super().__init__(**kw)
        self.transport = "tcp"
        self.ip = "127.0.0.1"
        self.cache_ports = True
        self.key = "0000-secret"
        self._conn_path = conn_path
        for name in ("shell", "iopub", "stdin", "control", "hb"):
            setattr(self, f"{name}_port", 0)

    def write_connection_file(self, jupyter_session=""):
        # Emulate ipc channel-index assignment (1..5).
        self.shell_port, self.iopub_port, self.stdin_port = 1, 2, 3
        self.control_port, self.hb_port = 4, 5
        with open(self._conn_path, "w") as fh:
            json.dump(self.get_connection_info(), fh)

    def get_connection_info(self):
        return {
            "transport": self.transport,
            "ip": self.ip,
            "key": self.key,
            "signature_scheme": "hmac-sha256",
            "kernel_name": "python3",
            "shell_port": self.shell_port,
            "iopub_port": self.iopub_port,
            "stdin_port": self.stdin_port,
            "control_port": self.control_port,
            "hb_port": self.hb_port,
        }


class FakeResult:
    def __init__(self, ok=True, exit_code=0, stderr="", stdout=""):
        self.ok = ok
        self.exit_code = exit_code
        self.stderr_text = stderr
        self.stdout_text = stdout

    def check(self):
        if not self.ok:
            raise RuntimeError(f"command failed: {self.stderr_text}")


class FakeProcess:
    def __init__(self):
        self._done = threading.Event()
        self.exit_code = None
        self.signals: list[str] = []

    def wait(self, timeout=None):
        self._done.wait(timeout)
        return FakeResult(exit_code=self.exit_code or 0)

    def signal(self, name):
        self.signals.append(name)

    def kill(self):
        self.signals.append("SIGKILL")
        self.exit_code = -9
        self._done.set()


class FakeFS:
    def __init__(self):
        self.files: dict[str, str] = {}

    def write_text(self, path, data):
        self.files[path] = data


class FakeSandbox:
    """Records interactions; ipykernel is 'already installed', sockets 'ready'."""

    id = "sbx-unit-test"

    def __init__(self, dial_factory=None):
        self.fs = FakeFS()
        self.exec_calls: list[tuple] = []
        self.start_calls: list[tuple] = []
        self.process = FakeProcess()
        self.closed = False
        self._dial_factory = dial_factory

    def exec(self, *argv, **kw):
        self.exec_calls.append(argv)
        return FakeResult(ok=True)

    def start(self, *argv, **kw):
        self.start_calls.append((argv, kw))
        return self.process

    def dial(self, path):
        if self._dial_factory is not None:
            return self._dial_factory(path)
        return _NullDial()

    def close(self):
        self.closed = True


class _NullDial:
    """A no-op dial connection used for the preflight probe in unit tests."""

    def write(self, data):
        return len(data)

    def read(self, n):
        return b""

    def close(self):
        pass


def make_provisioner(tmp_path, sandbox, **config):
    import tenki_sandbox

    # from tenki_sandbox import Sandbox; Sandbox.create(**opts) -> our fake
    def _create(**opts):
        sandbox.create_opts = opts
        return sandbox

    tenki_sandbox.Sandbox.create = staticmethod(_create)

    ks = KernelSpec(
        argv=["python3", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        language="python",
        env={},
        display_name="test",
    )
    km = FakeKernelManager(str(tmp_path / "local-conn.json"))
    return TenkiProvisioner(parent=km, kernel_id="k1", kernel_spec=ks, **config), km


# --------------------------------------------------------------------------- tests


async def test_pre_launch_switches_to_ipc(tmp_path):
    prov, km = make_provisioner(tmp_path, FakeSandbox())
    kw = await prov.pre_launch(env={})

    assert km.transport == "ipc"
    assert km.cache_ports is False
    assert km.ip == prov._local_prefix
    # connection command targets the guest-side connection file
    assert kw["cmd"] == [
        "python3",
        "-m",
        "ipykernel_launcher",
        "-f",
        "/home/tenki/k1-connection.json",
    ]
    assert prov.connection_info["transport"] == "ipc"
    assert prov.connection_info["shell_port"] == 1


async def test_launch_provisions_and_bridges(tmp_path):
    sandbox = FakeSandbox()
    prov, km = make_provisioner(tmp_path, sandbox, cpu_cores=4, memory_mb=8192)

    kw = await prov.pre_launch(env={})
    cmd = kw.pop("cmd")
    info = await prov.launch_kernel(cmd, **kw)

    # sandbox sized from config
    assert sandbox.create_opts["cpu_cores"] == 4
    assert sandbox.create_opts["memory_mb"] == 8192
    assert sandbox.create_opts["allow_inbound"] is False

    # guest-side connection file written, differing only in the ip prefix
    remote = json.loads(sandbox.fs.files["/home/tenki/k1-connection.json"])
    assert remote["ip"] == "/home/tenki/k1-k"
    assert remote["key"] == info["key"]
    assert remote["shell_port"] == info["shell_port"]

    # kernel launched with the substituted argv in the guest home
    (argv, start_kw), = [(a, k) for a, k in sandbox.start_calls]
    assert argv[:3] == ("python3", "-m", "ipykernel_launcher")
    assert start_kw["cwd"] == "/home/tenki"

    # local channel sockets are bound by the proxy
    for ch in ("shell", "iopub", "stdin", "control", "hb"):
        port = info[f"{ch}_port"]
        assert os.path.exists(f"{prov._local_prefix}-{port}")

    assert await prov.poll() is None  # still running

    await prov.cleanup()
    assert sandbox.closed is True
    assert prov.has_process is False
    assert not os.path.exists(f"{prov._local_prefix}-1")  # sockets cleaned up


async def test_signals_forwarded(tmp_path):
    sandbox = FakeSandbox()
    prov, km = make_provisioner(tmp_path, sandbox)
    kw = await prov.pre_launch(env={})
    await prov.launch_kernel(kw.pop("cmd"), **kw)

    await prov.send_signal(signal.SIGINT)
    assert "SIGINT" in sandbox.process.signals

    await prov.kill()
    assert "SIGKILL" in sandbox.process.signals
    assert await prov.wait() == -9

    await prov.cleanup()


async def test_ipykernel_install_retries_on_pep668(tmp_path):
    """A PEP 668 'externally-managed' failure retries with --break-system-packages."""
    sandbox = FakeSandbox()
    pip_calls: list[tuple] = []

    def fake_exec(*argv, **kw):
        sandbox.exec_calls.append(argv)
        if argv[:4] == ("python3", "-m", "pip", "install"):
            pip_calls.append(argv)
            if "--break-system-packages" not in argv:
                return FakeResult(ok=False, exit_code=1, stderr="externally-managed-environment")
            return FakeResult(ok=True)
        if argv[1:3] == ("-c", "import ipykernel"):
            return FakeResult(ok=False, exit_code=1)  # not installed -> triggers install
        return FakeResult(ok=True)

    sandbox.exec = fake_exec  # type: ignore[assignment]
    prov, km = make_provisioner(tmp_path, sandbox)
    kw = await prov.pre_launch(env={})
    await prov.launch_kernel(kw.pop("cmd"), **kw)

    assert len(pip_calls) == 2
    assert "--break-system-packages" in pip_calls[1]
    await prov.cleanup()


async def test_launch_fails_clearly_when_dial_unavailable(tmp_path):
    from tenki_sandbox import CapabilityUnavailableError

    sandbox = FakeSandbox()

    def _boom(_path):
        raise CapabilityUnavailableError("dial")

    sandbox.dial = _boom  # type: ignore[assignment]
    prov, km = make_provisioner(tmp_path, sandbox)
    kw = await prov.pre_launch(env={})
    with pytest.raises(RuntimeError, match="dial"):
        await prov.launch_kernel(kw.pop("cmd"), **kw)
    await prov.cleanup()


def test_ipc_proxy_bridges_bytes(tmp_path):
    """A local unix-socket client reaches a guest 'echo' socket via dial()."""

    def dial_factory(remote_path):
        near, far = socket.socketpair()

        def echo():
            try:
                while True:
                    data = far.recv(4096)
                    if not data:
                        break
                    far.sendall(data)  # echo back
            finally:
                far.close()

        threading.Thread(target=echo, daemon=True).start()
        return _SocketDial(near)

    sandbox = FakeSandbox(dial_factory=dial_factory)
    # Unix-domain socket paths are length-limited; use a short dir, not tmp_path.
    import tempfile

    sock_dir = tempfile.mkdtemp(prefix="tk-", dir="/tmp")
    local_path = os.path.join(sock_dir, "chan-1")
    proxy = IpcSocketProxy(sandbox, [(local_path, "/home/tenki/remote-1")])
    proxy.start()
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(5)
        client.connect(local_path)
        client.sendall(b"ping-through-tenki")
        assert client.recv(4096) == b"ping-through-tenki"
        client.close()
    finally:
        proxy.close()


class _SocketDial:
    """Adapts a socket to the DialConn read/write/close surface used by the proxy."""

    def __init__(self, sock):
        self._sock = sock

    def write(self, data):
        self._sock.sendall(data)

    def read(self, n):
        return self._sock.recv(n)

    def close(self):
        try:
            self._sock.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        self._sock.close()
