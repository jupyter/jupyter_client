================
Kernel providers
================

.. note::
   This is a new interface under development, and may still change.
   Not all Jupyter applications use this yet.
   See :ref:`kernelspecs` for the established way of discovering kernel types.

Creating a kernel provider
==========================

By writing a kernel provider, you can extend how Jupyter applications discover
and start kernels. For example, you could find kernels in an environment system
like conda, or kernels on remote systems which you can access.

To write a kernel provider, subclass
:class:`jupyter_client.discovery.KernelProviderBase`, giving your provider an ID
and overriding two methods.

.. class:: MyKernelProvider

   .. attribute:: id

      A short string identifying this provider. Cannot contain forward slash
      (``/``).

   .. method:: find_kernels()

      Get the available kernel types this provider knows about.
      Return an iterable of 2-tuples: (name, attributes).
      *name* is a short string identifying the kernel type.
      *attributes* is a dictionary with information to allow selecting a kernel.

   .. method:: make_manager(name)

      Prepare and return a :class:`~jupyter_client.KernelManager` instance
      ready to start a new kernel instance of the type identified by *name*.
      The input will be one of the names given by :meth:`find_kernels`.

For example, imagine we want to tell Jupyter about kernels for a new language
called *oblong*::

    # oblong_provider.py
    from jupyter_client.discovery import KernelProviderBase
    from jupyter_client import KernelManager
    from shutil import which

    class OblongKernelProvider(KernelProviderBase):
        id = 'oblong'

        def find_kernels(self):
            if not which('oblong-kernel'):
                return  # Check it's available

            # Two variants - for a real kernel, these could be something like
            # different conda environments.
            yield 'standard', {
                'display_name': 'Oblong (standard)',
                'language': {'name': 'oblong'},
                'argv': ['oblong-kernel'],
            }
            yield 'rounded', {
                'display_name': 'Oblong (rounded)',
                'language': {'name': 'oblong'},
                'argv': ['oblong-kernel'],
            }

        def make_manager(self, name):
            if name == 'standard':
                return KernelManager(kernel_cmd=['oblong-kernel'],
                                     extra_env={'ROUNDED': '0'})
            elif name == 'rounded':
                return KernelManager(kernel_cmd=['oblong-kernel'],
                                     extra_env={'ROUNDED': '1'})
            else:
                raise ValueError("Unknown kernel %s" % name)

You would then register this with an *entry point*. In your ``setup.py``, put
something like this::

    setup(...
        entry_points = {
        'jupyter_client.kernel_providers' : [
            # The name before the '=' should match the id attribute
            'oblong = oblong_provider:OblongKernelProvider',
        ]
    })

Finding kernel types
====================

To find and start kernels in client code, use
:class:`jupyter_client.discovery.KernelFinder`. This uses multiple kernel
providers to find available kernels. Like a kernel provider, it has methods
``find_kernels`` and ``make_manager``. The kernel names it works
with have the provider ID as a prefix, e.g. ``oblong/rounded`` (from the example
above).

::

    from jupyter_client.discovery import KernelFinder
    kf = KernelFinder.from_entrypoints()

    ## Find available kernel types
    for name, attributes in kf.find_kernels():
        print(name, ':', attributes['display_name'])
    # oblong/standard : Oblong (standard)
    # oblong/rounded : Oblong(rounded)
    # ...

    ## Start a kernel by name
    manager = kf.make_manager('oblong/standard')
    manager.start_kernel()

.. module:: jupyter_client.discovery

.. autoclass:: KernelFinder

   .. automethod:: from_entrypoints

   .. automethod:: find_kernels

   .. automethod:: make_manager

Kernel providers included in ``jupyter_client``
===============================================

``jupyter_client`` includes two kernel providers:

.. autoclass:: KernelSpecProvider

   .. seealso:: :ref:`kernelspecs`

.. autoclass:: IPykernelProvider

Glossary
========

Kernel instance
  A running kernel, a process which can accept ZMQ connections from frontends.
  Its state includes a namespace and an execution counter.

Kernel type
  The software to run a kernel instance, along with the context in which a
  kernel starts. One kernel type allows starting multiple, initially similar
  kernel instances. For instance, one kernel type may be associated with one
  conda environment containing ``ipykernel``. The same kernel software in
  another environment would be a different kernel type. Another software package
  for a kernel, such as ``IRkernel``, would also be a different kernel type.

Kernel provider
  A Python class to discover kernel types and allow a client to start instances
  of those kernel types. For instance, one kernel provider might find conda
  environments containing ``ipykernel`` and allow starting kernel instances in
  these environments.
