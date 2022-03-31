Pending Kernels
===============

*Added in 7.1.0*

In scenarios where an kernel takes a long time to start (e.g. kernels running
remotely), it can be advantageous to immediately return the kernel's model and
ID from key methods like ``.start_kernel()`` and ``.shutdown_kernel()``. The
kernel will continue its task without blocking other managerial actions.

This intermediate state is called a **"pending kernel"**.

How they work
-------------

When ``.start_kernel()`` or ``.shutdown_kernel()`` is called, a ``Future`` is
created under the ``KernelManager.ready`` property. This property can be
awaited anytime to ensure that the kernel moves out of its pending state, e.g.:

.. code-block:: python

    # await a Kernel Manager's `.ready` property to
    # block further action until the kernel is out
    # of its pending state.
    await kernel_manager.ready

Once the kernel is finished pending, ``.ready.done()`` will be ``True`` and
either 1) ``.ready.result()`` will return ``None`` or 2) ``.ready.exception()``
will return a raised exception

Using pending kernels
---------------------

The most common way to interact with pending kernels is through the ``
MultiKernelManager``—the object that manages a collection of kernels—by setting
its ``use_pending_kernels`` trait to ``True``. Pending kernels are "opt-in";
they are not used by default in the ``MultiKernelManager``.

When ``use_pending_kernels`` is ``True``, the following changes are made to the
``MultiKernelManager``:

1. ``start_kernel`` and ``stop_kernel`` return immediately while running the
    pending task in a background thread.
2. The following methods raise a ``RuntimeError`` if a kernel is pending:
    * ``restart_kernel``
    * ``interrupt_kernel``
    * ``shutdown_kernel``
3. ``shutdown_all`` will wait for all pending kernels to become ready before
    attempting to shut them down.
