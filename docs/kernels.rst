.. _kernels:

==========================
Making kernels for Jupyter
==========================

A 'kernel' is a program that runs and introspects the user's code. IPython
includes a kernel for Python code, and people have written kernels for
`several other languages <https://github.com/jupyter/jupyter/wiki/Jupyter-kernels>`_.

At kernel startup, Jupyter passes the kernel a connection file. This specifies
how to set up communications with the frontend.

There are three options for writing a kernel:

1. You can reuse the IPython kernel machinery to handle the communications, and
   just describe how to execute your code. This is much simpler if the target
   language can be driven from Python. See :doc:`wrapperkernels` for details.
2. You can implement the kernel machinery in your target language. This is more
   work initially, but the people using your kernel might be more likely to
   contribute to it if it's in the language they know.
3. You can use the `xeus <https://github.com/jupyter-xeus/xeus>`_ library that is
   a C++ implementation of the Jupyter kernel protocol. Kernel authors only need to
   implement the language-specific logic in their implementation
   (execute code, auto-completion...). This is the simplest
   solution if your target language can be driven from C or C++: e.g. if it has
   a C-API like most scripting languages. Check out the
   `xeus documentation <https://xeus.readthedocs.io/>`_ for more details.
   Examples of kernels based on xeus include:

   - `xeus-cling <https://github.com/jupyter-xeus/xeus-cling>`_
   - `xeus-python <https://github.com/jupyter-xeus/xeus-python>`_
   - `JuniperKernel <https://github.com/JuniperKernel/JuniperKernel>`_

Connection files
================

Your kernel will be given the path to a connection file when it starts (see
:ref:`kernelspecs` for how to specify the command line arguments for your kernel).
This file, which is accessible only to the current user, will contain a JSON
dictionary looking something like this::

    {
      "control_port": 50160,
      "shell_port": 57503,
      "transport": "tcp",
      "signature_scheme": "hmac-sha256",
      "stdin_port": 52597,
      "hb_port": 42540,
      "ip": "127.0.0.1",
      "iopub_port": 40885,
      "key": "a0436f6c-1916-498b-8eb9-e81ab9368e84"
    }

The ``transport``, ``ip`` and five ``_port`` fields specify five ports which the
kernel should bind to using `ZeroMQ <http://zeromq.org/>`_. For instance, the
address of the shell socket in the example above would be::

    tcp://127.0.0.1:57503

New ports are chosen at random for each kernel started.

``signature_scheme`` and ``key`` are used to cryptographically sign messages, so
that other users on the system can't send code to run in this kernel. See
:ref:`wire_protocol` for the details of how this signature is calculated.

Handling messages
=================

After reading the connection file and binding to the necessary sockets, the
kernel should go into an event loop, listening on the hb (heartbeat), control
and shell sockets.

:ref:`Heartbeat <kernel_heartbeat>` messages should be echoed back immediately
on the same socket - the frontend uses this to check that the kernel is still
alive.

Messages on the control and shell sockets should be parsed, and their signature
validated. See :ref:`wire_protocol` for how to do this.

The kernel will send messages on the iopub socket to display output, and on the
stdin socket to prompt the user for textual input.

.. seealso::

   :doc:`messaging`
     Details of the different sockets and the messages that come over them

   `Creating Language Kernels for IPython <http://andrew.gibiansky.com/blog/ipython/ipython-kernels/>`_
     A blog post by the author of `IHaskell <https://github.com/gibiansky/IHaskell>`_,
     a Haskell kernel

   `simple_kernel <https://github.com/dsblank/simple_kernel>`_
     A simple example implementation of the kernel machinery in Python


.. _kernelspecs:

Kernel specs
============

A kernel identifies itself to IPython by creating a directory, the name of which
is used as an identifier for the kernel. These may be created in a number of
locations:

+--------+--------------------------------------------+-----------------------------------+
|        | Unix                                       | Windows                           |
+========+============================================+===================================+
| System | ``/usr/share/jupyter/kernels``             | ``%PROGRAMDATA%\jupyter\kernels`` |
|        |                                            |                                   |
|        | ``/usr/local/share/jupyter/kernels``       |                                   |
+--------+--------------------------------------------+-----------------------------------+
| Env    |                          ``{sys.prefix}/share/jupyter/kernels``                |
+--------+--------------------------------------------+-----------------------------------+
| User   | ``~/.local/share/jupyter/kernels`` (Linux) | ``%APPDATA%\jupyter\kernels``     |
|        |                                            |                                   |
|        | ``~/Library/Jupyter/kernels`` (Mac)        |                                   |
+--------+--------------------------------------------+-----------------------------------+

The user location takes priority over the system locations, and the case of the
names is ignored, so selecting kernels works the same way whether or not the
filesystem is case sensitive.
Since kernelspecs show up in URLs and other places,
a kernelspec is required to have a simple name, only containing ASCII letters,
ASCII numbers, and the simple separators: ``-`` hyphen, ``.`` period, ``_``
underscore.

Other locations may also be searched if the :envvar:`JUPYTER_PATH` environment
variable is set.

Inside the kernel directory, three types of files are presently used:
``kernel.json``, ``kernel.js``, and logo image files. Currently, no other
files are used, but this may change in the future.

Inside the directory, the most important file is *kernel.json*. This should be a
JSON serialised dictionary containing the following keys and values:

- **argv**: A list of command line arguments used to start the kernel. The text
  ``{connection_file}`` in any argument will be replaced with the path to the
  connection file.
- **display_name**: The kernel's name as it should be displayed in the UI.
  Unlike the kernel name used in the API, this can contain arbitrary unicode
  characters.
- **language**: The name of the language of the kernel.
  When loading notebooks, if no matching kernelspec key (may differ across machines)
  is found, a kernel with a matching ``language`` will be used.
  This allows a notebook written on any Python or Julia kernel to be properly associated
  with the user's Python or Julia kernel, even if they aren't listed under the
  same name as the author's.
- **interrupt_mode** (optional): May be either ``signal`` or ``message`` and
  specifies how a client is supposed to interrupt cell execution on this kernel,
  either by sending an interrupt ``signal`` via the operating system's
  signalling facilities (e.g. ``SIGINT`` on POSIX systems), or by sending an
  ``interrupt_request`` message on the control channel (see
  :ref:`msging_interrupt`). If this is not specified
  the client will default to ``signal`` mode.
- **env** (optional): A dictionary of environment variables to set for the kernel.
  These will be added to the current environment variables before the kernel is
  started.  Existing environment variables can be referenced using ``${<ENV_VAR>}`` and
  will be substituted with the corresponding value.  Administrators should note that use
  of ``${<ENV_VAR>}`` can expose sensitive variables and should use only in controlled
  circumstances.
- **metadata** (optional): A dictionary of additional attributes about this
  kernel; used by clients to aid in kernel selection. Metadata added
  here should be namespaced for the tool reading and writing that metadata.

For example, the kernel.json file for IPython looks like this::

    {
     "argv": ["python3", "-m", "IPython.kernel",
              "-f", "{connection_file}"],
     "display_name": "Python 3",
     "language": "python"
    }

To see the available kernel specs, run::

    jupyter kernelspec list

To start the terminal console or the Qt console with a specific kernel::

    jupyter console --kernel bash
    jupyter qtconsole --kernel bash

The notebook offers you the available kernels in a dropdown menu from the 'New'
button.
