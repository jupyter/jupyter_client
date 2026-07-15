"""Install a kernelspec that launches kernels via :class:`TenkiProvisioner`.

Usage::

    python -m tenki_provisioner.kernelspec install --name tenki-python \
        --display-name "Python (Tenki Sandbox)" --cpu 4 --memory-mb 8192

This writes a ``kernel.json`` with a ``kernel_provisioner`` metadata stanza so
Jupyter routes the kernel through the Tenki provisioner.
"""

from __future__ import annotations

import argparse
import json
import sys

from jupyter_client.kernelspec import KernelSpecManager


def build_kernel_json(display_name: str, config: dict) -> dict:
    return {
        "argv": ["python3", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": display_name,
        "language": "python",
        # ipykernel supports message-based interrupt; the provisioner also
        # forwards real signals, so "signal" works too.
        "interrupt_mode": "signal",
        "metadata": {
            "kernel_provisioner": {
                "provisioner_name": "tenki-provisioner",
                "config": config,
            }
        },
    }


def install(args: argparse.Namespace) -> int:
    config: dict = {"cpu_cores": args.cpu, "memory_mb": args.memory_mb}
    if args.image:
        config["image"] = args.image
    if args.idle_timeout_minutes:
        config["idle_timeout_minutes"] = args.idle_timeout_minutes

    kernel_json = build_kernel_json(args.display_name, config)

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "kernel.json").write_text(json.dumps(kernel_json, indent=2))
        dest = KernelSpecManager().install_kernel_spec(
            tmp, kernel_name=args.name, user=args.user, prefix=args.prefix
        )
    print(f"Installed kernelspec '{args.name}' -> {dest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("install", help="Install the Tenki kernelspec.")
    p.add_argument("--name", default="tenki-python", help="Kernelspec name.")
    p.add_argument(
        "--display-name", default="Python (Tenki Sandbox)", help="UI display name."
    )
    p.add_argument("--cpu", type=int, default=2, help="vCPUs for the sandbox.")
    p.add_argument("--memory-mb", type=int, default=4096, help="Memory (MiB).")
    p.add_argument("--image", default="", help="Sandbox image (optional).")
    p.add_argument(
        "--idle-timeout-minutes", type=int, default=0, help="Idle auto-terminate."
    )
    p.add_argument("--user", action="store_true", help="Install into the user dir.")
    p.add_argument("--prefix", default=None, help="Install prefix (e.g. sys.prefix).")
    p.set_defaults(func=install)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
