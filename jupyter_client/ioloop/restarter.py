"""A basic in process kernel monitor with autorestarting.

This watches a kernel's state using KernelManager.is_alive and auto
restarts the kernel if it dies.
"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
import time

from jupyter_core.utils import ensure_async

from ..restarter import KernelRestarter


class IOLoopKernelRestarter(KernelRestarter):
    """Monitor and autorestart a kernel."""

    _poll_task: asyncio.Task | None = None
    _running = False

    def start(self) -> None:
        """Start the polling of the kernel."""
        if not self._poll_task:
            assert self.parent is not None
            assert isinstance(self.parent.loop, asyncio.AbstractEventLoop)
            self._poll_task = self.parent.loop.create_task(self._poll_loop())
            self._running = True

    async def _poll_loop(self) -> None:
        while self._running:
            await ensure_async(self.poll())  # type:ignore[func-returns-value]
            await asyncio.sleep(0.01)

    def stop(self) -> None:
        """Stop the kernel polling."""
        if self._poll_task is not None:
            self._poll_task = None
            self._running = False


class AsyncIOLoopKernelRestarter(IOLoopKernelRestarter):
    """An async io loop kernel restarter."""

    async def poll(self) -> None:  # type:ignore[override]
        """Poll the kernel."""
        if self.debug:
            self.log.debug("Polling kernel...")
        is_alive = await self.kernel_manager.is_alive()
        now = time.time()
        if not is_alive:
            self._last_dead = now
            if self._restarting:
                self._restart_count += 1
            else:
                self._restart_count = 1

            if self._restart_count > self.restart_limit:
                self.log.warning("AsyncIOLoopKernelRestarter: restart failed")
                self._fire_callbacks("dead")
                self._restarting = False
                self._restart_count = 0
                self.stop()
            else:
                newports = self.random_ports_until_alive and self._initial_startup
                self.log.info(
                    "AsyncIOLoopKernelRestarter: restarting kernel (%i/%i), %s random ports",
                    self._restart_count,
                    self.restart_limit,
                    "new" if newports else "keep",
                )
                self._fire_callbacks("restart")
                await self.kernel_manager.restart_kernel(now=True, newports=newports)
                self._restarting = True
        else:
            # Since `is_alive` only tests that the kernel process is alive, it does not
            # indicate that the kernel has successfully completed startup. To solve this
            # correctly, we would need to wait for a kernel info reply, but it is not
            # necessarily appropriate to start a kernel client + channels in the
            # restarter. Therefore, we use "has been alive continuously for X time" as a
            # heuristic for a stable start up.
            # See https://github.com/jupyter/jupyter_client/pull/717 for details.
            stable_start_time = self.stable_start_time
            if self.kernel_manager.provisioner:
                stable_start_time = self.kernel_manager.provisioner.get_stable_start_time(
                    recommended=stable_start_time
                )
            if self._initial_startup and now - self._last_dead >= stable_start_time:
                self._initial_startup = False
            if self._restarting and now - self._last_dead >= stable_start_time:
                self.log.debug("AsyncIOLoopKernelRestarter: restart apparently succeeded")
                self._restarting = False
