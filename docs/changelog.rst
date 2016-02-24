.. _changelog:

=========================
Changes in Jupyter Client
=========================

4.2
===

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
