kernel provisioner apis
=======================

.. seealso::

   :doc:`/provisioning`

.. module:: jupyter_client.provisioning.provisioner_base

.. autoclass:: KernelProvisionerBase

   .. attribute:: kernel_spec

      The kernel specification associated with the provisioned kernel (see :ref:`kernelspecs`).

   .. attribute:: kernel_id

      The provisioned kernel's ID.

   .. attribute:: connection_info

      The provisioned kernel's connection information.


   .. autoproperty:: has_process

   .. automethod:: poll

   .. automethod:: wait

   .. automethod:: send_signal

   .. automethod:: kill

   .. automethod:: terminate

   .. automethod:: launch_kernel

   .. automethod:: cleanup

   .. automethod:: shutdown_requested

   .. automethod:: pre_launch

   .. automethod:: post_launch

   .. automethod:: get_provisioner_info

   .. automethod:: load_provisioner_info

   .. automethod:: get_shutdown_wait_time

   .. automethod:: _finalize_env

   .. automethod:: __apply_env_substitutions

.. module:: jupyter_client.provisioning.local_provisioner

.. autoclass:: LocalProvisioner

.. module:: jupyter_client.provisioning.factory

.. autoclass:: KernelProvisionerFactory

    .. attribute:: default_provisioner_name

       Indicates the name of the provisioner to use when no kernel_provisioner entry is present in the kernel specification.  This value can also be specified via the environment variable ``JUPYTER_DEFAULT_PROVISIONER_NAME``.

    .. automethod:: is_provisioner_available

    .. automethod:: create_provisioner_instance
