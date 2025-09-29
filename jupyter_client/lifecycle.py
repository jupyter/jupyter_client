"""Kernel lifecycle state management for Jupyter kernel managers.

This module provides a state machine mixin for tracking kernel lifecycle states
across different kernel management operations. It's designed to work with any
kernel manager that follows the KernelManagerABC interface.

Basic Usage
-----------

To add lifecycle state tracking to a kernel manager::

    from jupyter_client.lifecycle import KernelManagerStateMixin
    from jupyter_client.manager import KernelManager

    class StatefulKernelManager(KernelManagerStateMixin, KernelManager):
        pass

    # The mixin automatically tracks state during kernel operations
    manager = StatefulKernelManager()
    print(manager.lifecycle_state)  # "unknown"

    await manager.start_kernel()
    print(manager.lifecycle_state)  # "started"
    print(manager.is_started)       # True

State Transitions
-----------------

The state machine handles these automatic transitions:

- **start_kernel**: unknown → starting → started (or unknown on failure)
- **restart_kernel**: * → restarting → restarted (or unknown on failure)
- **shutdown_kernel**: * → terminating → dead (or unknown on failure)

States can also be checked using convenient properties::

    manager.is_unknown       # True if state is "unknown"
    manager.is_starting      # True if state is "starting"
    manager.is_started       # True if state is "started"
    manager.is_restarting    # True if state is "restarting"
    manager.is_restarted     # True if state is "restarted"
    manager.is_terminating   # True if state is "terminating"
    manager.is_dead          # True if state is "dead"

Advanced Usage
--------------

The state machine can be used with custom kernel managers and supports
both synchronous and asynchronous operations::

    class CustomKernelManager(KernelManagerStateMixin):
        def start_kernel(self):
            # Custom start logic
            return "started"

        async def restart_kernel(self):
            # Custom async restart logic
            return "restarted"

Manual state management is also supported::

    manager.set_lifecycle_state(LifecycleState.STARTED)
    manager.lifecycle_state = LifecycleState.DEAD

Error Handling
--------------

When kernel operations fail, the state is automatically reset to "unknown"::

    class FailingKernelManager(KernelManagerStateMixin):
        def start_kernel(self):
            raise RuntimeError("Start failed")

    manager = FailingKernelManager()
    try:
        manager.start_kernel()
    except RuntimeError:
        pass

    print(manager.lifecycle_state)  # "unknown"
"""

import asyncio
import enum
from functools import wraps
from typing import Callable

from traitlets import HasTraits, Unicode, observe


class LifecycleState(str, enum.Enum):
    """Enumeration of kernel lifecycle states.

    This enum inherits from str to allow direct string comparisons without
    needing to access the .value attribute::

        assert LifecycleState.UNKNOWN == "unknown"
        assert "started" == LifecycleState.STARTED

    States:
        UNKNOWN: Initial state or state after errors
        STARTING: Kernel is in the process of starting
        STARTED: Kernel has been started successfully
        RESTARTING: Kernel is in the process of restarting
        RESTARTED: Kernel has been restarted successfully
        TERMINATING: Kernel is in the process of shutting down
        DEAD: Kernel has been shut down
    """

    UNKNOWN = "unknown"
    STARTING = "starting"
    STARTED = "started"
    RESTARTING = "restarting"
    RESTARTED = "restarted"
    TERMINATING = "terminating"
    DEAD = "dead"


def state_transition(start_state: LifecycleState, end_state: LifecycleState):
    """Decorator to handle state transitions for kernel manager methods.

    This decorator automatically manages state transitions around method calls,
    setting the start state before the method executes and the end state after
    successful completion. If the method raises an exception, the state is set
    to UNKNOWN.

    Parameters
    ----------
    start_state : LifecycleState
        The state to set before calling the method
    end_state : LifecycleState
        The state to set after successful method completion

    Returns
    -------
    Callable
        The decorated method with automatic state management

    Examples
    --------
    >>> class Manager:
    ...     lifecycle_state = LifecycleState.UNKNOWN
    ...
    ...     @state_transition(LifecycleState.STARTING, LifecycleState.STARTED)
    ...     def start_kernel(self):
    ...         return "kernel started"
    ...
    >>> manager = Manager()
    >>> result = manager.start_kernel()
    >>> assert manager.lifecycle_state == LifecycleState.STARTED
    """

    def decorator(method: Callable) -> Callable:
        @wraps(method)
        async def async_wrapper(self, *args, **kwargs):
            # Set the starting state
            self.lifecycle_state = start_state
            try:
                # Call the original method
                result = await method(self, *args, **kwargs)
                # Set the end state on success
                self.lifecycle_state = end_state
                return result
            except Exception:
                # Set to unknown state on failure
                self.lifecycle_state = LifecycleState.UNKNOWN
                raise

        @wraps(method)
        def sync_wrapper(self, *args, **kwargs):
            # Set the starting state
            self.lifecycle_state = start_state
            try:
                # Call the original method
                result = method(self, *args, **kwargs)
                # Set the end state on success
                self.lifecycle_state = end_state
                return result
            except Exception:
                # Set to unknown state on failure
                self.lifecycle_state = LifecycleState.UNKNOWN
                raise

        # Return the appropriate wrapper based on whether the method is async
        if asyncio.iscoroutinefunction(method):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class KernelManagerStateMixin(HasTraits):
    """Mixin class that adds lifecycle state tracking to kernel managers.

    This mixin automatically tracks kernel lifecycle states during standard
    kernel management operations. It works with any kernel manager that follows
    the KernelManagerABC interface and uses method name conventions for kernel
    operations.

    The mixin uses the `__init_subclass__` hook to automatically wrap kernel
    management methods (start_kernel, restart_kernel, shutdown_kernel) with
    state transition decorators.

    Attributes
    ----------
    lifecycle_state : Unicode
        The current lifecycle state of the kernel. Configurable trait that
        defaults to LifecycleState.UNKNOWN.

    Examples
    --------
    Basic usage with inheritance::

        class MyKernelManager(KernelManagerStateMixin, SomeBaseManager):
            def start_kernel(self):
                # Your start logic here
                pass

        manager = MyKernelManager()
        print(manager.is_unknown)  # True

        manager.start_kernel()
        print(manager.is_started)  # True

    Custom state management::

        manager = MyKernelManager()
        manager.set_lifecycle_state(LifecycleState.STARTED)
        assert manager.lifecycle_state == "started"

    State checking::

        if manager.is_started:
            manager.restart_kernel()
        elif manager.is_dead:
            manager.start_kernel()

    Notes
    -----
    - State transitions are logged via the manager's logger if available
    - Failed operations automatically reset state to UNKNOWN
    - The mixin supports both sync and async kernel operations
    - Method wrapping only occurs if the methods exist on the class
    """

    lifecycle_state = Unicode(
        default_value=LifecycleState.UNKNOWN, help="The current lifecycle state of the kernel"
    ).tag(config=True)

    @observe("lifecycle_state")
    def _lifecycle_state_changed(self, change):
        """Log lifecycle state changes for debugging.

        Parameters
        ----------
        change : dict
            The change notification dict from traitlets containing
            'old' and 'new' values
        """
        old_state = change["old"]
        new_state = change["new"]
        kernel_id = getattr(self, "kernel_id", "unknown")
        if hasattr(self, "log"):
            self.log.debug(f"Kernel {kernel_id} state changed: {old_state} -> {new_state}")

    def __init_subclass__(cls, **kwargs):
        """Automatically wrap kernel management methods when the class is subclassed.

        This method is called when a class inherits from KernelManagerStateMixin
        and automatically applies state transition decorators to standard kernel
        management methods if they exist.

        Parameters
        ----------
        **kwargs
            Additional keyword arguments passed to parent __init_subclass__
        """
        super().__init_subclass__(**kwargs)

        # Wrap start_kernel method if it exists
        if hasattr(cls, "start_kernel"):
            original_start = cls.start_kernel
            cls.start_kernel = state_transition(LifecycleState.STARTING, LifecycleState.STARTED)(
                original_start
            )

        # Wrap restart_kernel method if it exists
        if hasattr(cls, "restart_kernel"):
            original_restart = cls.restart_kernel
            cls.restart_kernel = state_transition(
                LifecycleState.RESTARTING, LifecycleState.RESTARTED
            )(original_restart)

        # Wrap shutdown_kernel method if it exists
        if hasattr(cls, "shutdown_kernel"):
            original_shutdown = cls.shutdown_kernel
            cls.shutdown_kernel = state_transition(LifecycleState.TERMINATING, LifecycleState.DEAD)(
                original_shutdown
            )

    # State checking properties

    @property
    def is_starting(self) -> bool:
        """True if kernel is in starting state."""
        return self.lifecycle_state == LifecycleState.STARTING

    @property
    def is_started(self) -> bool:
        """True if kernel is in started state."""
        return self.lifecycle_state == LifecycleState.STARTED

    @property
    def is_restarting(self) -> bool:
        """True if kernel is in restarting state."""
        return self.lifecycle_state == LifecycleState.RESTARTING

    @property
    def is_restarted(self) -> bool:
        """True if kernel is in restarted state."""
        return self.lifecycle_state == LifecycleState.RESTARTED

    @property
    def is_terminating(self) -> bool:
        """True if kernel is in terminating state."""
        return self.lifecycle_state == LifecycleState.TERMINATING

    @property
    def is_dead(self) -> bool:
        """True if kernel is in dead state."""
        return self.lifecycle_state == LifecycleState.DEAD

    @property
    def is_unknown(self) -> bool:
        """True if kernel is in unknown state."""
        return self.lifecycle_state == LifecycleState.UNKNOWN

    # State management methods

    def set_lifecycle_state(self, state: LifecycleState) -> None:
        """Manually set the lifecycle state.

        Parameters
        ----------
        state : LifecycleState
            The state to set

        Examples
        --------
        >>> manager.set_lifecycle_state(LifecycleState.STARTED)
        >>> assert manager.is_started
        """
        self.lifecycle_state = state
