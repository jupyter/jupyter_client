"""
Patch for jupyter_client.MultiKernelManager which is invalid syntax on
Python 2.7, so need to be in a separate file and conditionally patched.
"""

import asyncio
from inspect import iscoroutinefunction

@asyncio.coroutine
def start_kernel_async(self, kernel_name=None, **kwargs):
    """Start a new kernel.

    The caller can pick a kernel_id by passing one in as a keyword arg,
    otherwise one will be generated using new_kernel_id().

    The kernel ID for the newly started kernel is returned.
    """

    kernel_id, kernel_name, km = self._start_kernel(kernel_name, **kwargs)

    if iscoroutinefunction(km.start_kernel):
        yield from km.start_kernel(**kwargs)
    else:
        km.start_kernel(**kwargs)

    self._kernels[kernel_id] = km
    return kernel_id
