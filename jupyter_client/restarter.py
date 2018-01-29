"""A basic kernel monitor with autorestarting.

This watches a kernel's state using KernelManager.is_alive and auto
restarts the kernel if it dies.

It is an incomplete base class, and must be subclassed.
"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from traitlets.config.configurable import LoggingConfigurable
from traitlets import (
    Instance, Float, Dict, Bool, Integer,
)
import time
try:
    from queue import Empty  # Python 3
except ImportError:
    from Queue import Empty  # Python 2


class KernelRestarter(LoggingConfigurable):
    """Monitor and autorestart a kernel."""

    kernel_manager = Instance('jupyter_client.KernelManager')

    debug = Bool(False, config=True,
        help="""Whether to include every poll event in debugging output.

        Has to be set explicitly, because there will be *a lot* of output.
        """
    )

    time_to_dead = Float(3.0, config=True,
        help="""Kernel heartbeat interval in seconds."""
    )

    startup_time = Float(20.0, config=True,
        help="""Waiting time for kernel_info reply during initial startup"""
    )

    restart_limit = Integer(5, config=True,
        help="""The number of consecutive autorestarts before the kernel is presumed dead."""
    )

    random_ports_until_alive = Bool(True, config=True,
        help="""Whether to choose new random ports when restarting before the kernel is alive."""
    )

    kernel_monitor_enabled = Bool(True, config=True,
        help="""Whether to restart kernel with new ports if response is not received within startup_time timeout"""
    )
    _restarting = Bool(False)
    _restart_count = Integer(0)
    _initial_startup = Bool(True)
    _kernel_info_requested = Bool(False)
    _kernel_info_timeout = Float(0)
    kernel_client = None

    callbacks = Dict()
    def _callbacks_default(self):
        return dict(restart=[], dead=[])

    def start(self):
        """Start the polling of the kernel."""
        raise NotImplementedError("Must be implemented in a subclass")

    def stop(self):
        """Stop the kernel polling."""
        raise NotImplementedError("Must be implemented in a subclass")

    def add_callback(self, f, event='restart'):
        """register a callback to fire on a particular event

        Possible values for event:

          'restart' (default): kernel has died, and will be restarted.
          'dead': restart has failed, kernel will be left dead.

        """
        self.callbacks[event].append(f)

    def remove_callback(self, f, event='restart'):
        """unregister a callback to fire on a particular event

        Possible values for event:

          'restart' (default): kernel has died, and will be restarted.
          'dead': restart has failed, kernel will be left dead.

        """
        try:
            self.callbacks[event].remove(f)
        except ValueError:
            pass

    def _fire_callbacks(self, event, **kwargs):
        """fire our callbacks for a particular event"""
        for callback in self.callbacks[event]:
            try:
                callback(**kwargs)
            except Exception as e:
                self.log.error("KernelRestarter: %s callback %r failed", event, callback, exc_info=True)

    def poll(self):
        if self.debug:
            self.log.debug('Polling kernel...')
        if not self.kernel_manager.is_alive() or self.is_kernel_response_timedout():
            if self._restarting:
                self._restart_count += 1
            else:
                self._restart_count = 1
            if self._restart_count >= self.restart_limit:
                self.log.warning("KernelRestarter: restart failed")
                self._fire_callbacks('dead')
                self._restarting = False
                self._restart_count = 0
                self.stop()
            else:
                newports = self.random_ports_until_alive and self._initial_startup
                self.log.info('KernelRestarter: restarting kernel (%i/%i), %s random ports',
                    self._restart_count,
                    self.restart_limit,
                    'new' if newports else 'keep'
                )
                self.kernel_manager.restart_kernel(now=True, newports=newports)
                self._fire_callbacks('restart', newports=newports)
                self._restarting = True
        else:
            if self._restarting:
                self.log.debug("KernelRestarter: restart apparently succeeded")
            self._restarting = False

    def is_kernel_response_timedout(self):
        if self.kernel_monitor_enabled and self.startup_time > 0:
            if not self._kernel_info_requested:
                self.kernel_client = self.kernel_manager.client()
                self._kernel_info_timeout = time.time() + self.startup_time
                self.log.debug("KernelRestarter: Requesting kernel info")
                self.kernel_client.kernel_info()
                self._kernel_info_requested = True
            if time.time() > self._kernel_info_timeout:
                self.log.warning("KernelRestarter: Kernel Info reply timed out. Restarting kernel")
                self._kernel_info_requested = False
                self._restarting = True
                return True
            try:
                msg = self.kernel_client.shell_channel.get_msg(block=True, timeout=0)
            except Empty:
                self.log.debug("KernelRestarter: No message received")
                pass
            else:
                if msg['msg_type'] == 'kernel_info_reply':
                    self.kernel_client._handle_kernel_info_reply(msg)
                    self.log.info("KernelRestarter: Kernel info reply received")
                    self.kernel_monitor_enabled = False
                    if self._initial_startup:
                        self._initial_startup = False
        return False