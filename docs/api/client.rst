client - communicating with kernels
===================================

.. currentmodule:: jupyter_client

.. seealso::

   :doc:`/messaging`
     The Jupyter messaging specification

.. autoclass:: KernelClient

   .. automethod:: load_connection_file

   .. automethod:: load_connection_info

   .. automethod:: start_channels

   .. automethod:: execute

   .. automethod:: complete

   .. automethod:: inspect

   .. automethod:: history

   .. automethod:: comm_info

   .. automethod:: is_complete

   .. automethod:: input

   .. automethod:: shutdown

.. autoclass:: BlockingKernelClient

   .. automethod:: execute_interactive

   .. automethod:: get_shell_msg

   .. automethod:: get_iopub_msg

   .. automethod:: get_stdin_msg

   .. automethod:: get_control_msg

   .. automethod:: wait_for_ready

   .. automethod:: is_alive

.. autoclass:: AsyncKernelClient

   :class:`AsyncKernelClient` is identical to :class:`BlockingKernelClient` but the methods described above are async.
