Managing multiple kernels
=========================

``MultiKernelManager`` and ``AsyncMultiKernelManager`` share one ZeroMQ context
between the kernels they manage by default. To configure the number of native
I/O threads in that context, set a positive ``MultiKernelManager.io_threads``
value before the context is created. For example, in a Jupyter configuration
file::

    c.MultiKernelManager.io_threads = 4

The default remains one I/O thread. The setting applies to both synchronous and
asyncio contexts created by the manager, including a replacement for a closed
context. Changing it does not resize an existing context. A live context passed
explicitly to the manager keeps its own options. When ``shared_context=False``,
the individual kernel managers continue to create their own contexts.

Additional I/O threads can help when native I/O processing, such as CURVE
decryption, is the bottleneck. They do not guarantee an even distribution of
connections, prevent IOPub queue overflow, or change the kernel's own threads.
