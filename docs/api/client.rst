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

   .. automethod:: get_shell_msg

   .. automethod:: get_iopub_msg

   .. automethod:: get_stdin_msg

.. autoclass:: BlockingKernelClient

   .. automethod:: execute_interactive
