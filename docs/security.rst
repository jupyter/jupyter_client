.. _security:

================================
Transport security for kernels
================================

.. versionadded:: 8.9

By default, the ZMQ sockets used to communicate with kernels (shell, IOPub,
stdin, control, heartbeat) are bound to local TCP ports with no
transport-level encryption. Any process on the same host that can reach
those ports can connect and read messages, including all IOPub output.

`CurveZMQ <https://rfc.zeromq.org/spec/26/>`_ adds elliptic-curve
encryption and authentication at the ZMQ transport layer. When enabled, the
``KernelManager`` generates a keypair, writes it into the kernel's connection
file, and configures all sockets as a CurveZMQ server. Clients must present
the correct server public key to connect; unauthenticated connections are
silently dropped before any data is delivered.

.. note::

    CurveZMQ is only available when pyzmq was compiled against a libzmq that
    includes libsodium. You can verify this with::

        python -c "import zmq; print(zmq.has('curve'))"

    If this prints ``False``, the ``transport_encryption`` setting has no
    effect and attempts to set it to ``'auto'`` or ``'required'`` will raise
    a :exc:`traitlets.TraitError`.

.. note::

    ``transport_encryption`` applies to both the ``tcp`` and ``ipc``
    transports. IPC sockets also rely on filesystem permissions for access
    control, but CurveZMQ can be layered on top for defense in depth.


The ``transport_encryption`` setting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Transport encryption is controlled by the
``KernelManager.transport_encryption`` traitlet, which accepts three values:

``'disabled'`` (default)
    No CurveZMQ keys are generated. All kernel sockets are unencrypted.

``'auto'``
    Keys are generated **only when the kernelspec declares support** via
    ``metadata.supported_encryption: 'curve'``. Kernelspecs that do not
    declare this field are started without encryption, so the setting is safe
    to enable globally without breaking existing kernels.

``'required'``
    Keys are always generated. Startup fails with a :exc:`RuntimeError` if
    the kernelspec does not declare ``metadata.supported_encryption: 'curve'``,
    so kernels that have not been updated to handle the connection-file keys
    are never started unencrypted.

To enable encryption for all kernels that support it, add the following to
your configuration:

.. code:: python

    c.KernelManager.transport_encryption = "auto"

To enforce encryption and refuse to start kernels that do not declare support:

.. code:: python

    c.KernelManager.transport_encryption = "required"


Kernelspec requirements
~~~~~~~~~~~~~~~~~~~~~~~

A kernel must declare CurveZMQ support in its ``kernel.json`` before the
``KernelManager`` will provision keys for it:

.. code:: JSON

    {
        "argv": ["python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "Python 3",
        "language": "python",
        "metadata": {
            "supported_encryption": "curve"
        }
    }

When ``transport_encryption`` is ``'auto'``, kernelspecs without this field
are started normally without encryption. When it is ``'required'``, their
startup is refused.

.. note::

    When updating a previously installed kernel to a version that supports
    encryption you may need to re-install the kernelspec or manually add the
    ``supported_encryption`` metadata field. If you subsequently decide to
    downgrade, you will need to remove this field as otherwise the kernel will
    silently fail to connect.


Connection file fields
~~~~~~~~~~~~~~~~~~~~~~

When ``transport_encryption`` is active the connection file written to disk
will contain two additional fields alongside the usual port and key fields:

``curve_publickey``
    Z85-encoded 40-character ASCII string holding the server's CurveZMQ
    public key.

``curve_secretkey``
    Z85-encoded 40-character ASCII string holding the server's CurveZMQ
    secret key.

Kernel implementations must read these fields from the connection file and
apply them to their ZMQ sockets before binding. See :ref:`kernels` for the
full description of the connection file format.


Implementing curve support in a kernel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A kernel that wants to be compatible with ``transport_encryption`` must apply
the keypair to every socket it binds. In Python, using pyzmq, that looks like:

.. code:: python

    import json
    import zmq

    with open(connection_file_path) as f:
        cfg = json.load(f)

    ctx = zmq.Context()
    shell = ctx.socket(zmq.ROUTER)

    if "curve_publickey" in cfg and "curve_secretkey" in cfg:
        shell.curve_secretkey = cfg["curve_secretkey"].encode()
        shell.curve_publickey = cfg["curve_publickey"].encode()
        shell.curve_server = True

    shell.bind(f"tcp://{cfg['ip']}:{cfg['shell_port']}")

The same pattern applies to the IOPub, stdin, control, and heartbeat sockets.
Setting ``curve_server = True`` on a bound socket causes ZMQ to require
CurveZMQ authentication on every incoming connection; unauthenticated clients
are rejected automatically.

Kernels based on `ipykernel <https://ipykernel.readthedocs.io/>`_ v7.3+ handle
this automatically when the connection file contains the curve fields.

.. seealso::

   :ref:`kernels`
     Connection file format and kernelspec reference.

   :ref:`provisioning`
     How ``LocalProvisioner`` generates and injects curve keys during
     kernel startup.
