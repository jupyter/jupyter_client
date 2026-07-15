"""A :class:`~jupyter_client.provisioning.KernelProvisionerBase` that launches
Jupyter kernels inside `Tenki Sandbox <https://tenki.cloud>`_ microVMs.

Each kernel gets its own disposable, isolated Linux microVM.  The kernel talks
to ``jupyter_client`` over the ZeroMQ ``ipc`` transport; the five channel
sockets are bridged from the local machine into the guest with the Tenki
Sandbox SDK's ``dial`` primitive (see :mod:`tenki_provisioner._proxy`).  The
integration therefore depends only on the ``tenki-sandbox`` SDK -- no ssh, no
CLI, no inbound networking.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import signal
import tempfile
from typing import Any

from jupyter_client.connect import KernelConnectionInfo
from jupyter_client.provisioning.provisioner_base import KernelProvisionerBase
from traitlets import Bool, Dict, Int, List, Unicode

from ._proxy import IpcSocketProxy

#: Working directory inside a Tenki Sandbox guest.  File operations are rooted
#: here and absolute paths outside it are rejected by the service.
REMOTE_HOME = "/home/tenki"

#: Jupyter's five ZeroMQ channels, in the order the connection info names them.
_CHANNELS = ("shell", "iopub", "stdin", "control", "hb")


class TenkiProvisioner(KernelProvisionerBase):
    """Provision a Jupyter kernel inside a Tenki Sandbox microVM.

    The provisioner is configured through the ``config`` stanza of a kernelspec's
    ``kernel_provisioner`` metadata, or programmatically via traitlets, e.g.::

        {
          "argv": ["python3", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
          "language": "python",
          "metadata": {
            "kernel_provisioner": {
              "provisioner_name": "tenki-provisioner",
              "config": {"cpu_cores": 4, "memory_mb": 8192}
            }
          }
        }
    """

    # --- Sandbox sizing / creation -----------------------------------------
    cpu_cores = Int(2, help="vCPUs for the sandbox microVM (1-16).").tag(config=True)
    memory_mb = Int(4096, help="Memory for the sandbox microVM in MiB.").tag(config=True)
    image = Unicode(
        "", help="Sandbox image reference. Empty uses the service default."
    ).tag(config=True)
    allow_outbound = Bool(
        True,
        help="Allow the guest outbound network access (needed to pip install ipykernel).",
    ).tag(config=True)
    idle_timeout_minutes = Int(
        0, help="Terminate the sandbox after this many idle minutes (0 = service default)."
    ).tag(config=True)

    # --- Kernel launch -----------------------------------------------------
    kernel_argv = List(
        Unicode(),
        default_value=["python3", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        help="Command run inside the guest. '{connection_file}' is substituted.",
    ).tag(config=True)
    python_executable = Unicode(
        "python3", help="Interpreter used inside the guest for dependency checks."
    ).tag(config=True)
    install_ipykernel = Bool(
        True, help="pip install ipykernel in the guest if it is not importable."
    ).tag(config=True)
    extra_pip_packages = List(
        Unicode(), default_value=[], help="Extra packages to pip install in the guest."
    ).tag(config=True)
    env = Dict(
        value_trait=Unicode(), help="Environment variables to set for the kernel process."
    ).tag(config=True)

    # --- Auth (falls back to TENKI_API_KEY / TENKI_API_ENDPOINT envs) ------
    auth_token = Unicode(None, allow_none=True).tag(config=True)
    base_url = Unicode(None, allow_none=True).tag(config=True)

    # --- Timeouts ----------------------------------------------------------
    create_timeout = Int(180, help="Seconds to wait for the sandbox to become ready.").tag(
        config=True
    )
    install_timeout = Int(240, help="Seconds allowed for installing ipykernel.").tag(
        config=True
    )
    kernel_ready_timeout = Int(
        60, help="Seconds to wait for the kernel's channel sockets to appear."
    ).tag(config=True)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._sandbox: Any = None
        self._process: Any = None
        self._proxy: IpcSocketProxy | None = None
        self._returncode: int | None = None
        self._tmpdir: str | None = None
        self._local_prefix: str | None = None
        self._remote_prefix: str | None = None
        self._remote_conn_path: str | None = None

    # ------------------------------------------------------------------ utils
    @staticmethod
    async def _run(fn, *args, **kwargs):
        """Run a blocking SDK call off the event loop."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))

    @property
    def has_process(self) -> bool:
        return self._process is not None

    def _identifier(self) -> str:
        return (self.kernel_id or "kernel").replace("/", "_")

    # -------------------------------------------------------------- lifecycle
    async def pre_launch(self, **kwargs: Any) -> dict[str, Any]:
        """Switch the kernel to the ``ipc`` transport and stage connection files.

        We point the local (client-side) connection info at a private temp
        directory and record a parallel guest-side prefix under ``REMOTE_HOME``.
        The two connection files are identical except for that path prefix, so
        the HMAC key and channel indices line up on both ends.
        """
        km = self.parent
        if km is None:
            msg = "TenkiProvisioner must be owned by a KernelManager."
            raise RuntimeError(msg)

        # Unix-domain socket paths are length-limited (~104 chars on macOS), so
        # root them under a short directory rather than the (long) system temp
        # dir. The channel sockets live here as "<tmpdir>/k-<N>".
        short_base = "/tmp" if os.path.isdir("/tmp") else tempfile.gettempdir()
        self._tmpdir = tempfile.mkdtemp(prefix="tk-", dir=short_base)
        os.chmod(self._tmpdir, 0o700)
        self._local_prefix = os.path.join(self._tmpdir, "k")

        # Drive the kernel over ipc with locally-controlled socket paths.
        km.transport = "ipc"
        km.ip = self._local_prefix
        km.cache_ports = False
        for name in _CHANNELS:
            setattr(km, f"{name}_port", 0)

        env = kwargs.get("env", {})
        km.write_connection_file(jupyter_session=env.get("JPY_SESSION_NAME", ""))
        self.connection_info = km.get_connection_info()

        ident = self._identifier()
        self._remote_prefix = f"{REMOTE_HOME}/{ident}-k"
        self._remote_conn_path = f"{REMOTE_HOME}/{ident}-connection.json"

        argv = [
            arg.replace("{connection_file}", self._remote_conn_path)
            for arg in self.kernel_argv
        ]
        return await super().pre_launch(cmd=argv, **kwargs)

    async def launch_kernel(self, cmd: list[str], **kwargs: Any) -> KernelConnectionInfo:
        """Create the sandbox, launch the kernel, and start the socket proxy."""
        await self._run(self._provision_sandbox)
        await self._run(self._ensure_ipykernel)
        await self._run(self._write_remote_connection_file)
        await self._run(self._start_kernel_process, cmd)
        await self._run(self._await_kernel_sockets)
        self._start_proxy()
        return self.connection_info

    # ------------------------------------------------------------ blocking bits
    def _provision_sandbox(self) -> None:
        from tenki_sandbox import Sandbox

        opts: dict[str, Any] = {
            "name": f"jupyter-{self._identifier()}"[:63],
            "cpu_cores": self.cpu_cores,
            "memory_mb": self.memory_mb,
            "allow_outbound": self.allow_outbound,
            "allow_inbound": False,
            "wait": True,
            "timeout": self.create_timeout,
            "metadata": {"purpose": "jupyter-kernel", "kernel_id": self.kernel_id or ""},
        }
        if self.image:
            opts["image"] = self.image
        if self.idle_timeout_minutes:
            opts["idle_timeout_minutes"] = self.idle_timeout_minutes
        if self.auth_token:
            opts["auth_token"] = self.auth_token
        if self.base_url:
            opts["base_url"] = self.base_url
        self.log.info("Creating Tenki Sandbox for kernel %s", self.kernel_id)
        self._sandbox = Sandbox.create(**opts)
        self.log.info("Sandbox %s ready", getattr(self._sandbox, "id", "?"))

    def _ensure_ipykernel(self) -> None:
        sb = self._sandbox
        need = list(self.extra_pip_packages)
        if self.install_ipykernel:
            probe = sb.exec(self.python_executable, "-c", "import ipykernel", timeout=30)
            if not probe.ok:
                need.append("ipykernel")
        if not need:
            return
        self.log.info("Installing in sandbox: %s", " ".join(need))
        result = sb.exec(
            self.python_executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            *need,
            timeout=self.install_timeout,
        )
        result.check()

    def _write_remote_connection_file(self) -> None:
        remote_info = dict(self.connection_info)
        remote_info["ip"] = self._remote_prefix
        # bytes -> str for JSON (curve keys, if present, are already str here).
        payload = json.dumps(
            {k: (v.decode() if isinstance(v, bytes) else v) for k, v in remote_info.items()}
        )
        self._sandbox.fs.write_text(self._remote_conn_path, payload)

    def _start_kernel_process(self, cmd: list[str]) -> None:
        guest_env = {}
        if self.kernel_spec is not None and self.kernel_spec.env:
            guest_env.update(self.kernel_spec.env)
        guest_env.update(self.env)
        self.log.info("Launching kernel in sandbox: %s", " ".join(cmd))
        self._process = self._sandbox.start(*cmd, cwd=REMOTE_HOME, env=guest_env or None)

        def _reap() -> None:
            try:
                result = self._process.wait()
                self._returncode = result.exit_code
            except Exception:  # noqa: BLE001
                self._returncode = 1

        import threading

        threading.Thread(target=_reap, name="tenki-kernel-reap", daemon=True).start()

    def _await_kernel_sockets(self) -> None:
        """Block until the kernel has bound all five ipc sockets in the guest."""
        paths = [f"{self._remote_prefix}-{self.connection_info[f'{c}_port']}" for c in _CHANNELS]
        test = " && ".join(f'test -S "{p}"' for p in paths)
        script = (
            f"for i in $(seq {self.kernel_ready_timeout}); do "
            f"if {test}; then exit 0; fi; sleep 1; done; exit 1"
        )
        result = self._sandbox.exec("sh", "-c", script, timeout=self.kernel_ready_timeout + 10)
        if not result.ok:
            msg = (
                "Kernel did not bind its channel sockets within "
                f"{self.kernel_ready_timeout}s. stderr: {result.stderr_text}"
            )
            raise RuntimeError(msg)

    def _start_proxy(self) -> None:
        mappings = [
            (
                f"{self._local_prefix}-{self.connection_info[f'{c}_port']}",
                f"{self._remote_prefix}-{self.connection_info[f'{c}_port']}",
            )
            for c in _CHANNELS
        ]
        self._proxy = IpcSocketProxy(self._sandbox, mappings, log=self.log)
        self._proxy.start()

    # ------------------------------------------------------------- process ctl
    async def poll(self) -> int | None:
        if self._process is None:
            return 0
        return self._returncode

    async def wait(self) -> int | None:
        if self._process is not None:
            await self._run(self._process.wait)
        return self._returncode

    async def send_signal(self, signum: int) -> None:
        if self._process is None:
            return
        if signum == signal.SIGKILL:
            await self.kill()
            return
        try:
            name = signal.Signals(signum).name  # e.g. "SIGINT"
        except ValueError:
            return
        await self._run(self._process.signal, name)

    async def kill(self, restart: bool = False) -> None:
        if self._process is not None:
            await self._run(self._process.kill)

    async def terminate(self, restart: bool = False) -> None:
        if self._process is not None:
            try:
                await self._run(self._process.signal, "SIGTERM")
            except Exception:  # noqa: BLE001
                pass

    async def cleanup(self, restart: bool = False) -> None:
        """Tear down the proxy and terminate the sandbox microVM."""
        if self._proxy is not None:
            self._proxy.close()
            self._proxy = None
        sandbox, self._sandbox = self._sandbox, None
        if sandbox is not None:
            self.log.info("Terminating sandbox for kernel %s", self.kernel_id)
            await self._run(lambda: _safe_close(sandbox))
        self._process = None
        if self._tmpdir is not None:
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None

    async def get_provisioner_info(self) -> dict[str, Any]:
        info = await super().get_provisioner_info()
        info["sandbox_id"] = getattr(self._sandbox, "id", None)
        return info


def _safe_close(sandbox: Any) -> None:
    for method in ("close", "terminate"):
        fn = getattr(sandbox, method, None)
        if callable(fn):
            try:
                fn()
                return
            except Exception:  # noqa: BLE001
                continue
