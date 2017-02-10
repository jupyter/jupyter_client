.. _changelog:

=========================
Changes in Jupyter Client
=========================

5.0
===

5.0.0
-----

`5.0.0 on GitHub <https://github.com/jupyter/jupyter_client/milestones/5.0>`__

New features:

- Introduce :command:`jupyter run` command for running scripts with a kernel, for instance::

    jupyter run --kernel python3 myscript.py

- New method :meth:`.BlockingKernelClient.execute_interactive`
  for running code and capturing or redisplaying its output.
- New ``KernelManager.shutdown_wait_time`` configurable for adjusting the time
  for a kernel manager to wait after politely requesting shutdown
  before it resorts to forceful termination.

Fixes:

- Set sticky bit on connection-file directory to avoid getting cleaned up.
- :func:`jupyter_client.launcher.launch_kernel` passes through additional options to the underlying Popen,
  matching :meth:`KernelManager.start_kernel`.
- Check types of ``buffers`` argument in :meth:`.Session.send`,
  so that TypeErrors are raised immediately,
  rather than in the eventloop.

Changes:

- In kernelspecs, if the executable is the string ``python`` (as opposed to an absolute path),
  ``sys.executable`` will be used rather than resolving ``python`` on PATH.
  This should enable Python-based kernels to install kernelspecs as part of wheels.
- kernelspec names are now validated.
  They should only include ascii letters and numbers, plus period, hyphen, and underscore.

Backward-incompatible changes:

- :py:class:`.datetime` objects returned in parsed messages are now always timezone-aware.
  Timestamps in messages without timezone info are interpreted as the local timezone,
  as this was the behavior in earlier versions.


4.4
===

4.4.0
-----

`4.4 on GitHub <https://github.com/jupyter/jupyter_client/milestones/4.4>`__

- Add :meth:`.KernelClient.load_connection_info` on KernelClient, etc. for loading connection info
  directly from a dict, not just from files.
- Include parent headers when adapting messages from older protocol implementations
  (treats parent headers the same as headers).
- Compatibility fixes in tests for recent changes in ipykernel.

4.3
===

4.3.0
-----

`4.3 on GitHub <https://github.com/jupyter/jupyter_client/milestones/4.3>`__

- Adds ``--sys-prefix`` argument to :command:`jupyter kernelspec install`,
  for better symmetry with :command:`jupyter nbextension install`, etc.

4.2
===

4.2.2
-----

`4.2.2 on GitHub <https://github.com/jupyter/jupyter_client/milestones/4.2.2>`__

- Another fix for the :func:`start_new_kernel` issue in 4.2.1 affecting slow-starting kernels.


4.2.1
-----

`4.2.1 on GitHub <https://github.com/jupyter/jupyter_client/milestones/4.2.1>`__

- Fix regression in 4.2 causing :func:`start_new_kernel`
  to fail while waiting for kernels to become available.


4.2.0
-----

`4.2.0 on GitHub <https://github.com/jupyter/jupyter_client/milestones/4.2>`__

- added :command:`jupyter kernelspec remove` for removing kernelspecs
- allow specifying the environment for kernel processes via the ``env`` argument
- added ``name`` field to connection files identifying the kernelspec name,
  so that consumers of connection files (alternate frontends) can identify the kernelspec in use
- added :meth:`KernelSpecManager.get_all_specs` for getting all kernelspecs more efficiently
- various improvements to error messages and documentation

4.1
===

4.1.0
-----

`4.1.0 on GitHub <https://github.com/jupyter/jupyter_client/milestones/4.1>`__

Highlights:

- Setuptools fixes for ``jupyter kernelspec``
- ``jupyter kernelspec list`` includes paths
- add :meth:`KernelManager.blocking_client`
- provisional implementation of ``comm_info`` requests from upcoming 5.1 release of the protocol

4.0
===

The first release of Jupyter Client as its own package.
