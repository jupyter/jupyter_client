"""Regression coverage for cached ports across local kernel restarts."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import asyncio
import json
import os
import socket
import subprocess
import sys
from subprocess import DEVNULL

import pytest

from jupyter_client import AsyncKernelManager
from jupyter_client.connect import LocalPortCache, port_names
from jupyter_client.kernelspec import KernelSpec


def make_manager(tmp_path, **kwargs):
    """Use the current interpreter and an isolated connection file."""
    km = AsyncKernelManager(connection_file=str(tmp_path / "kernel.json"), **kwargs)
    km._kernel_spec = KernelSpec(
        argv=[sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        display_name="port-restart-test",
        language="python",
    )
    return km


async def test_cached_random_ports_are_replaced_and_returned(tmp_path):
    """Refresh random ports while normal restart preparation retains them."""
    km = make_manager(tmp_path)
    cache = LocalPortCache.instance()
    initially_used = cache.currently_used_ports.copy()
    try:
        await km._async_pre_start_kernel()
        original = {name: getattr(km, name) for name in port_names}
        assert cache.currently_used_ports == initially_used | set(original.values())

        await km.provisioner.cleanup(restart=True)
        await km._async_pre_start_kernel()
        assert original == {name: getattr(km, name) for name in port_names}

        for _ in range(2):
            previous = {name: getattr(km, name) for name in port_names}
            km.cleanup_random_ports()
            await km._async_pre_start_kernel()
            replacement = {name: getattr(km, name) for name in port_names}
            assert set(replacement.values()).isdisjoint(previous.values())
            assert cache.currently_used_ports == initially_used | set(replacement.values())
            file_info = json.loads((tmp_path / "kernel.json").read_text())
            assert {name: file_info[name] for name in port_names} == replacement
    finally:
        await km.cleanup_resources()
    assert cache.currently_used_ports == initially_used


async def test_newports_recovers_from_an_occupied_startup_port(tmp_path, monkeypatch):
    """Restart a real ipykernel while another listener keeps its old port."""
    cache = LocalPortCache.instance()
    initially_used = cache.currently_used_ports.copy()
    real_pick = cache.find_available_port
    blockers = []

    def pick_and_occupy(ip):
        port = real_pick(ip)
        if not blockers:
            blocker = socket.socket()
            blocker.bind((ip, port))
            blocker.listen()
            blockers.append(blocker)
        return port

    monkeypatch.setattr(cache, "find_available_port", pick_and_occupy)
    km = make_manager(tmp_path)
    client = None
    try:
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        await km.start_kernel(stdout=DEVNULL, stderr=DEVNULL, **options)
        occupied_port = blockers[0].getsockname()[1]
        assert km.shell_port == occupied_port
        assert await asyncio.wait_for(km.provisioner.wait(), timeout=15) != 0

        await km.restart_kernel(now=True, newports=True)
        client = km.client()
        client.start_channels()
        await client.wait_for_ready(timeout=15)
        assert km.shell_port != occupied_port
        assert blockers[0].getsockname()[1] == occupied_port
        reply = await client.execute_interactive(
            "6 * 7",
            timeout=10,
            user_expressions={"result": "6 * 7"},
            output_hook=lambda msg: None,
        )
        assert reply["content"]["status"] == "ok"
        assert reply["content"]["user_expressions"]["result"]["data"]["text/plain"] == "42"
    finally:
        if client is not None:
            client.stop_channels()
        if km.has_kernel:
            await km.shutdown_kernel(now=True)
        else:
            await km.cleanup_resources()
        for blocker in blockers:
            blocker.close()
    assert cache.currently_used_ports == initially_used


async def test_partial_reallocation_failure_returns_new_reservations(tmp_path, monkeypatch):
    """A failed refresh retains old reservations and permits another attempt."""
    km = make_manager(tmp_path)
    cache = LocalPortCache.instance()
    initially_used = cache.currently_used_ports.copy()
    try:
        await km._async_pre_start_kernel()
        old_ports = {getattr(km, name) for name in port_names}
        real_pick = cache.find_available_port
        allocated = []

        def fail_third_allocation(ip):
            if len(allocated) == 2:
                raise OSError("test allocation failure")
            port = real_pick(ip)
            allocated.append(port)
            return port

        km.cleanup_random_ports()
        with monkeypatch.context() as patch:
            patch.setattr(cache, "find_available_port", fail_third_allocation)
            with pytest.raises(OSError, match="test allocation failure"):
                await km._async_pre_start_kernel()
        assert cache.currently_used_ports == initially_used | old_ports
        await km._async_pre_start_kernel()
        new_ports = {getattr(km, name) for name in port_names}
        assert old_ports.isdisjoint(new_ports)
        assert cache.currently_used_ports == initially_used | new_ports
    finally:
        await km.cleanup_resources()
    assert cache.currently_used_ports == initially_used


@pytest.mark.parametrize("refresh", [False, True])
async def test_connection_file_failure_returns_new_reservations(tmp_path, monkeypatch, refresh):
    """A failed connection-file write keeps only reservations it can clean up."""
    km = make_manager(tmp_path)
    cache = LocalPortCache.instance()
    initially_used = cache.currently_used_ports.copy()
    try:
        old_ports = set()
        if refresh:
            await km._async_pre_start_kernel()
            old_ports = {getattr(km, name) for name in port_names}
            km.cleanup_random_ports()
        requested = {name: getattr(km, name) for name in port_names}

        def fail_write(**kwargs):
            raise OSError("test write failure")

        with monkeypatch.context() as patch:
            patch.setattr(km, "write_connection_file", fail_write)
            with pytest.raises(OSError, match="test write failure"):
                await km._async_pre_start_kernel()
        assert {name: getattr(km, name) for name in port_names} == requested
        assert cache.currently_used_ports == initially_used | old_ports

        await km._async_pre_start_kernel()
        new_ports = {getattr(km, name) for name in port_names}
        assert old_ports.isdisjoint(new_ports)
        assert cache.currently_used_ports == initially_used | new_ports
    finally:
        await km.cleanup_resources()
    assert cache.currently_used_ports == initially_used


async def test_uncached_fixed_port_is_preserved(tmp_path):
    """Random-port cleanup leaves an explicitly configured uncached port alone."""
    cache = LocalPortCache.instance()
    initially_used = cache.currently_used_ports.copy()
    fixed_port = cache.find_available_port("127.0.0.1")
    km = make_manager(tmp_path, cache_ports=False, shell_port=fixed_port)
    try:
        await km._async_pre_start_kernel()
        km.cleanup_random_ports()
        await km._async_pre_start_kernel()
        assert km.shell_port == fixed_port
        assert cache.currently_used_ports == initially_used | {fixed_port}
    finally:
        await km.cleanup_resources()
        cache.return_port(fixed_port)
    assert cache.currently_used_ports == initially_used
