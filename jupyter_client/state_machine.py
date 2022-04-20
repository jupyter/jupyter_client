from transitions.extensions.asyncio import AsyncMachine

from jupyter_client.manager import AsyncKernelManager


KERNEL_STATES = [
    "unknown",
    "starting",
    "started",
    "terminating",
    "dead",
    "connecting",
    "connected",
    "disconnected",
]


KERNEL_TRANSITIONS = [
    {
        "trigger": "_launch_kernel",
        "source": ["unknown", "dead"],
        "dest": "started",
        "before": "to_starting",
    },
    # {
    #     "trigger": "start_heartbeat",
    #     "source": "started",
    #     "dest": "connected",
    #     "before": "to_connecting",
    # },
    {
        "trigger": "shutdown_kernel",
        "source": ["connected", "started"],
        "dest": "dead",
        "before": "to_terminating",
    },
]


class KernelStateMachine(AsyncMachine):
    """A State machine that maintains the kernel
    state from a kernel manager
    """

    def __init__(self, kernel_manager: AsyncKernelManager):
        super().__init__(
            model=kernel_manager,
            states=KERNEL_STATES,
            transitions=KERNEL_TRANSITIONS,
            initial="unknown",
        )

    # `transitions` tries to create *new* methods for each
    # trigger name. since we already have methods for these
    # methods, we'll wrap the methods instead.
    def _checked_assignment(self, kernel_manager, name, trigger):
        # Check that
        if hasattr(kernel_manager, name):
            predefined_func = getattr(kernel_manager, name)
            self.events[name].add_callback("before", predefined_func)
            setattr(kernel_manager, name, trigger)
        else:
            setattr(kernel_manager, name, trigger)
