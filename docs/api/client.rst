client - communicating with kernels
===================================

.. currentmodule:: jupyter_client

.. seealso::

   :doc:`/messaging`
     The Jupyter messaging specification

.. autoclass:: KernelClient

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
