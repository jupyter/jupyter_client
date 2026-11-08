"""Shared-context configuration and ownership tests."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import asyncio
import gc
from subprocess import PIPE

import pytest
import zmq
import zmq.asyncio
from traitlets import TraitError
from traitlets.config import Config

from jupyter_client.multikernelmanager import AsyncMultiKernelManager, MultiKernelManager
from jupyter_client.utils import ensure_async


@pytest.fixture(
    params=[(MultiKernelManager, zmq.Context), (AsyncMultiKernelManager, zmq.asyncio.Context)],
    ids=["sync", "async"],
)
def manager_types(request):
    return request.param


def test_default_io_threads(manager_types):
    manager_class, context_class = manager_types
    manager = manager_class()
    try:
        assert isinstance(manager.context, context_class)
        assert manager.context.get(zmq.IO_THREADS) == 1
    finally:
        manager.context.destroy(linger=0)


@pytest.mark.parametrize("io_threads", [1, 2, 4])
def test_configured_io_threads(manager_types, io_threads):
    manager_class, context_class = manager_types
    config = Config()
    config.MultiKernelManager.io_threads = io_threads
    manager = manager_class(config=config)
    try:
        assert isinstance(manager.context, context_class)
        assert manager.context.get(zmq.IO_THREADS) == io_threads
    finally:
        manager.context.destroy(linger=0)


@pytest.mark.parametrize("io_threads", [0, -1, None, "2", 1.5])
def test_invalid_io_threads(manager_types, io_threads):
    manager_class, _ = manager_types
    with pytest.raises(TraitError):
        manager_class(io_threads=io_threads)


@pytest.mark.parametrize("supplied", [False, True])
def test_recreated_context_uses_current_io_threads(manager_types, supplied):
    manager_class, context_class = manager_types
    kwargs = {"context": context_class(io_threads=2)} if supplied else {}
    manager = manager_class(io_threads=2, **kwargs)
    original = manager.context
    try:
        manager.io_threads = 4
        assert original.get(zmq.IO_THREADS) == 2
        original.destroy(linger=0)
        kernel = manager.kernel_manager_factory()
        assert manager.context is not original
        assert kernel.context is manager.context
        assert isinstance(manager.context, context_class)
        assert manager.context.get(zmq.IO_THREADS) == 4
    finally:
        manager.context.destroy(linger=0)


def test_supplied_context_keeps_options_and_ownership(manager_types):
    manager_class, context_class = manager_types
    context = context_class(io_threads=3)
    try:
        manager = manager_class(context=context, io_threads=4)
        assert manager.context is context
        assert context.get(zmq.IO_THREADS) == 3
        del manager
        gc.collect()
        assert not context.closed
    finally:
        context.destroy(linger=0)


def test_non_shared_contexts_keep_their_defaults(manager_types):
    manager_class, _ = manager_types
    manager = manager_class(shared_context=False, io_threads=4)
    kernels = [manager.kernel_manager_factory(), manager.kernel_manager_factory()]
    try:
        assert kernels[0].context is not kernels[1].context
        assert all(kernel.context.get(zmq.IO_THREADS) == 1 for kernel in kernels)
        assert not manager._created_context
    finally:
        for kernel in kernels:
            kernel.context.destroy(linger=0)


def test_shared_context_kernel_execution(manager_types):
    manager_class, _ = manager_types

    async def run():
        manager = manager_class(io_threads=2)
        clients = []
        try:
            for _ in range(2):
                kernel_id = await ensure_async(manager.start_kernel(stdout=PIPE, stderr=PIPE))
                kernel = manager.get_kernel(kernel_id)
                assert kernel.context is manager.context
                assert kernel.context.get(zmq.IO_THREADS) == 2
                client = kernel.client(context=manager.context)
                clients.append(client)
                client.start_channels()
                await ensure_async(client.wait_for_ready(timeout=30))
                outputs = []
                reply = await ensure_async(
                    client.execute_interactive("2 + 2", timeout=30, output_hook=outputs.append)
                )
                assert reply["content"]["status"] == "ok"
                assert any(
                    output["msg_type"] == "execute_result"
                    and output["content"]["data"]["text/plain"] == "4"
                    for output in outputs
                )
        finally:
            for client in clients:
                client.stop_channels()
            await ensure_async(manager.shutdown_all(now=True))
            manager.context.destroy(linger=0)

    asyncio.run(run())
