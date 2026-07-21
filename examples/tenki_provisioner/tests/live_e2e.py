"""Live end-to-end check: start a real kernel inside a Tenki Sandbox microVM,
execute code in it, and prove it ran remotely.

Requires a Tenki API key in the environment::

    export TENKI_API_KEY=tk_...
    python tests/live_e2e.py

Exits non-zero on any failure. This is intentionally a script (not a pytest
test) so it never runs — or bills — during ordinary `pytest` runs.
"""

from __future__ import annotations

import os
import queue
import socket
import sys
import uuid

from jupyter_client.manager import KernelManager


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    if not (os.environ.get("TENKI_API_KEY") or os.environ.get("TENKI_AUTH_TOKEN")):
        _fail("set TENKI_API_KEY (or TENKI_AUTH_TOKEN) first")

    local_host = socket.gethostname()
    kid = f"live-{uuid.uuid4().hex[:8]}"

    km = KernelManager(kernel_name="python3")
    km.kernel_id = kid
    # Route this kernel through the Tenki provisioner regardless of the
    # installed kernelspec, so the check is self-contained.
    config = {"cpu_cores": 2, "memory_mb": 4096}
    if os.environ.get("TENKI_PROJECT_ID"):
        config["project_id"] = os.environ["TENKI_PROJECT_ID"]
    km.kernel_spec.metadata["kernel_provisioner"] = {
        "provisioner_name": "tenki-provisioner",
        "config": config,
    }

    print(f"Starting kernel {kid} in a Tenki Sandbox microVM (local host: {local_host}) ...")
    km.start_kernel()
    kc = km.client()
    kc.start_channels()
    try:
        kc.wait_for_ready(timeout=180)
        print("Kernel is ready. Executing remote code ...")

        code = (
            "import socket, sys, platform\n"
            "print('HOST=' + socket.gethostname())\n"
            "print('PLATFORM=' + sys.platform)\n"
            "print('UNAME=' + platform.uname().release)\n"
            "print('SUM=' + str(6 * 7))\n"
        )
        msg_id = kc.execute(code)

        outputs: list[str] = []
        got_reply = False
        while True:
            try:
                msg = kc.get_iopub_msg(timeout=60)
            except queue.Empty:
                break
            if msg["parent_header"].get("msg_id") != msg_id:
                continue
            mtype = msg["msg_type"]
            content = msg["content"]
            if mtype == "stream":
                outputs.append(content["text"])
            elif mtype == "error":
                _fail("remote execution error:\n" + "\n".join(content["traceback"]))
            elif mtype == "status" and content["execution_state"] == "idle" and got_reply:
                break
            elif mtype == "execute_input":
                got_reply = True

        text = "".join(outputs)
        print("--- remote stdout ---")
        print(text.rstrip())
        print("---------------------")

        if "SUM=42" not in text:
            _fail("did not observe expected computation result (SUM=42)")
        remote_host = ""
        for line in text.splitlines():
            if line.startswith("HOST="):
                remote_host = line[len("HOST="):].strip()
        if not remote_host:
            _fail("could not read remote hostname")
        if remote_host == local_host:
            _fail(f"kernel appears to be local (host {remote_host} == {local_host})")

        print(f"PASS: kernel ran remotely on {remote_host!r} (local is {local_host!r}).")
    finally:
        print("Shutting down kernel and terminating microVM ...")
        kc.stop_channels()
        km.shutdown_kernel(now=True)


if __name__ == "__main__":
    main()
