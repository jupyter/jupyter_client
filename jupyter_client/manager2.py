"""Base class to manage a running kernel"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import absolute_import

from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
import logging
import os
import signal
import six
import subprocess
import sys
import time

log = logging.getLogger(__name__)

from traitlets.log import get_logger as get_app_logger

from .launcher2 import (
    make_connection_file, build_popen_kwargs, prepare_interrupt_event
)
from .localinterfaces import is_local_ip, local_ips, localhost


class KernelManager2ABC(six.with_metaclass(ABCMeta, object)):
    @abstractmethod
    def is_alive(self):
        """Check whether the kernel is currently alive (e.g. the process exists)
        """
        pass

    @abstractmethod
    def wait(self, timeout):
        """Wait for the kernel process to exit.

        If timeout is a number, it is a maximum time in seconds to wait.
        timeout=None means wait indefinitely.

        Returns True if the kernel is still alive after waiting, False if it
        exited (like is_alive()).
        """
        pass

    @abstractmethod
    def signal(self, signum):
        """Send a signal to the kernel."""
        pass

    @abstractmethod
    def interrupt(self):
        """Interrupt the kernel by sending it a signal or similar event

        Kernels can request to get interrupts as messages rather than signals.
        The manager is *not* expected to handle this.
        :meth:`.KernelClient2.interrupt` should send an interrupt_request or
        call this method as appropriate.
        """
        pass

    @abstractmethod
    def kill(self):
        """Forcibly terminate the kernel.

        This method may be used to dispose of a kernel that won't shut down.
        Working kernels should usually be shut down by sending shutdown_request
        from a client and giving it some time to clean up.
        """
        pass

    def cleanup(self):
        """Clean up any resources, such as files created by the manager."""
        pass

    @abstractmethod
    def get_connection_info(self):
        """Return a dictionary of connection information"""
        pass

    @abstractmethod
    def relaunch(self):
        """Attempt to relaunch the kernel using the same ports.

        This is meant to be called after the managed kernel has died. Calling
        it while the kernel is still alive has undefined behaviour.

        Returns True if this manager supports that.
        """
        pass


class KernelManager2(KernelManager2ABC):
    """Manages a single kernel in a subprocess on this host.

    This version starts kernels with Popen to listen on TCP sockets.

    Parameters
    ----------

    kernel_cmd : list of str
      The Popen command template to launch the kernel
    cwd : str
      The working directory to launch the kernel in
    extra_env : dict, optional
      Dictionary of environment variables to update the existing environment
    ip : str, optional
      Set the kernel\'s IP address [default localhost].
      If the IP address is something other than localhost, then
      Consoles on other machines will be able to connect
      to the Kernel, so be careful!
    """
    transport = 'tcp'

    def __init__(self, kernel_cmd, cwd, extra_env=None, ip=None):
        self.kernel_cmd = kernel_cmd
        self.cwd = cwd
        self.extra_env = extra_env
        if ip is None:
            ip = localhost()
        self.ip = ip
        self.log = get_app_logger()

        if self.transport == 'tcp' and not is_local_ip(ip):
            raise RuntimeError("Can only launch a kernel on a local interface. "
                               "Make sure that the '*_address' attributes are "
                               "configured properly. "
                               "Currently valid addresses are: %s" % local_ips()
                               )

        self.connection_file, self.connection_info = \
            make_connection_file(ip, self.transport)

        kw = build_popen_kwargs(kernel_cmd, self.connection_file,
                                extra_env, cwd)
        self._win_interrupt_evt = prepare_interrupt_event(kw['env'])

        # launch the kernel subprocess
        self.log.debug("Starting kernel: %s", kw['args'])
        self.kernel = subprocess.Popen(**kw)
        self.kernel.stdin.close()

    def wait(self, timeout):
        """"""
        if timeout is None:
            # Wait indefinitely
            self.kernel.wait()
            return False

        if six.PY3:
            try:
                self.kernel.wait(timeout)
                return False
            except subprocess.TimeoutExpired:
                return True
        else:
            pollinterval = 0.1
            for i in range(int(timeout / pollinterval)):
                if self.is_alive():
                    time.sleep(pollinterval)
                else:
                    return False
            return self.is_alive()

    def cleanup(self):
        """Clean up resources when the kernel is shut down"""
        # cleanup connection files on full shutdown of kernel we started
        try:
            os.remove(self.connection_file)
        except (IOError, OSError, AttributeError):
            pass

    def relaunch(self):
        """Attempt to relaunch the kernel using the same ports.

        This is meant to be called after the managed kernel has died. Calling
        it while the kernel is still alive has undefined behaviour.

        Returns True if this manager supports that.
        """
        kw = build_popen_kwargs(self.kernel_cmd, self.connection_file,
                                self.extra_env, self.cwd)
        prepare_interrupt_event(kw['env'], self._win_interrupt_evt)

        # launch the kernel subprocess
        self.log.debug("Starting kernel: %s", kw['args'])
        self.kernel = subprocess.Popen(**kw)
        self.kernel.stdin.close()
        return True

    def kill(self):
        """Kill the running kernel.
        """
        # Signal the kernel to terminate (sends SIGKILL on Unix and calls
        # TerminateProcess() on Win32).
        try:
            self.kernel.kill()
        except OSError as e:
            # In Windows, we will get an Access Denied error if the process
            # has already terminated. Ignore it.
            if sys.platform == 'win32':
                if e.winerror != 5:
                    raise
            # On Unix, we may get an ESRCH error if the process has already
            # terminated. Ignore it.
            else:
                from errno import ESRCH
                if e.errno != ESRCH:
                    raise

        # Block until the kernel terminates.
        self.kernel.wait()

    def interrupt(self):
        """Interrupts the kernel by sending it a signal.

        Unlike ``signal_kernel``, this operation is well supported on all
        platforms.

        Kernels may ask for interrupts to be delivered by a message rather than
        a signal. This method does *not* handle that. Use KernelClient.interrupt
        to send a message or a signal as appropriate.
        """
        if sys.platform == 'win32':
            from .win_interrupt import send_interrupt
            send_interrupt(self._win_interrupt_evt)
        else:
            self.signal(signal.SIGINT)

    def signal(self, signum):
        """Sends a signal to the process group of the kernel (this
        usually includes the kernel and any subprocesses spawned by
        the kernel).

        Note that since only SIGTERM is supported on Windows, this function is
        only useful on Unix systems.
        """
        if hasattr(os, "getpgid") and hasattr(os, "killpg"):
            try:
                pgid = os.getpgid(self.kernel.pid)
                os.killpg(pgid, signum)
                return
            except OSError:
                pass
        self.kernel.send_signal(signum)

    def is_alive(self):
        """Is the kernel process still running?"""
        return self.kernel.poll() is None

    def get_connection_info(self):
        return self.connection_info

class IPCKernelManager2(KernelManager2):
    """Start a kernel on this machine to listen on IPC (filesystem) sockets"""
    transport = 'ipc'

    def cleanup(self):
        ports = [v for (k, v) in self.connection_info.items()
                 if k.endswith('_port')]
        for port in ports:
            ipcfile = "%s-%i" % (self.connection_info['ip'], port)
            try:
                os.remove(ipcfile)
            except (IOError, OSError):
                pass

        super(IPCKernelManager2, self).cleanup()

def shutdown(client, manager, wait_time=5.0):
    """Shutdown a kernel using a client and a manager.

    Attempts a clean shutdown by sending a shutdown message. If the kernel
    hasn't exited in wait_time seconds, it will be killed. Set wait_time=None
    to wait indefinitely.
    """
    client.shutdown()
    if manager.wait(wait_time):
        # OK, we've waited long enough.
        log.debug("Kernel is taking too long to finish, killing")
        manager.kill()
    manager.cleanup()

def start_new_kernel(kernel_cmd, startup_timeout=60, cwd=None):
    """Start a new kernel, and return its Manager and a blocking client"""
    from .client2 import BlockingKernelClient2
    cwd = cwd or os.getcwd()

    km = KernelManager2(kernel_cmd, cwd=cwd)
    kc = BlockingKernelClient2(km.connection_info, manager=km)
    try:
        kc.wait_for_ready(timeout=startup_timeout)
    except RuntimeError:
        shutdown(kc, km)
        kc.close()
        raise

    return km, kc

@contextmanager
def run_kernel(kernel_cmd, **kwargs):
    """Context manager to create a kernel in a subprocess.

    The kernel is shut down when the context exits.

    Returns
    -------
    kernel_client: connected KernelClient instance
    """
    km, kc = start_new_kernel(kernel_cmd, **kwargs)
    try:
        yield kc
    finally:
        shutdown(kc, km)
        kc.close()
