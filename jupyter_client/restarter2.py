"""Machinery to monitor a KernelManager and restart the kernel if it dies
"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from tornado import ioloop
from traitlets.config.configurable import LoggingConfigurable
from traitlets import (
    Float,  Bool, Integer,
)

from .discovery import KernelFinder


class KernelRestarterBase(LoggingConfigurable):
    """Monitor and autorestart a kernel."""

    debug = Bool(False, config=True,
        help="""Whether to include every poll event in debugging output.

        Has to be set explicitly, because there will be *a lot* of output.
        """
    )

    time_to_dead = Float(3.0, config=True,
        help="""Kernel heartbeat interval in seconds."""
    )

    restart_limit = Integer(5, config=True,
        help="""The number of consecutive autorestarts before the kernel is presumed dead."""
    )

    random_ports_until_alive = Bool(True, config=True,
        help="""Whether to choose new random ports when restarting before the kernel is alive."""
    )
    _restarting = False
    _restart_count = 0
    _initial_startup = True

    def __init__(self, kernel_manager, kernel_type, kernel_finder=None, **kw):
        super(KernelRestarterBase, self).__init__(**kw)
        self.kernel_manager = kernel_manager
        self.kernel_type = kernel_type
        self.kernel_finder = kernel_finder or KernelFinder.from_entrypoints()
        self.callbacks = dict(restart=[], dead=[])

    def start(self):
        """Start monitoring the kernel."""
        raise NotImplementedError("Must be implemented in a subclass")

    def stop(self):
        """Stop monitoring."""
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

    def _fire_callbacks(self, event):
        """fire our callbacks for a particular event"""
        for callback in self.callbacks[event]:
            try:
                callback()
            except Exception as e:
                self.log.error("KernelRestarter: %s callback %r failed", event, callback, exc_info=True)

    def do_restart(self):
        """Called when the kernel has died"""
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
            self._fire_callbacks('restart')
            if newports:
                cwd = getattr(self.kernel_manager, 'cwd', None)  # :-/
                self.log.info("KernelRestarter: starting new manager (%i/%i)",
                              self._restart_count, self.restart_limit)
                self.kernel_manager.cleanup()
                self.kernel_manager = self.kernel_finder.launch(
                    self.kernel_type, cwd)
            else:
                self.log.info(
                    'KernelRestarter: restarting kernel (%i/%i), keeping ports',
                    self._restart_count, self.restart_limit)
                self.kernel_manager.relaunch()
            self._restarting = True

    def poll(self):
        if self.debug:
            self.log.debug('Polling kernel...')
        if not self.kernel_manager.is_alive():
            self.do_restart()
        else:
            if self._initial_startup:
                self._initial_startup = False
            if self._restarting:
                self.log.debug("KernelRestarter: restart apparently succeeded")
            self._restarting = False


class TornadoKernelRestarter(KernelRestarterBase):
    """Monitor a kernel using the tornado ioloop."""
    _pcallback = None

    def start(self):
        """Start the polling of the kernel."""
        if self._pcallback is None:
            self._pcallback = ioloop.PeriodicCallback(
                self.poll, 1000*self.time_to_dead,
            )
            self._pcallback.start()

    def stop(self):
        """Stop the kernel polling."""
        if self._pcallback is not None:
            self._pcallback.stop()
            self._pcallback = None

