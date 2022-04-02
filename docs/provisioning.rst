.. _provisioning:

Customizing the kernel's runtime environment
============================================

Kernel Provisioning
~~~~~~~~~~~~~~~~~~~

Introduced in the 7.0 release, Kernel Provisioning enables the ability
for third parties to manage the lifecycle of a kernel's runtime
environment. By implementing and configuring a *kernel provisioner*,
third parties now have the ability to provision kernels for different
environments, typically managed by resource managers like Kubernetes,
Hadoop YARN, Slurm, etc. For example, a *Kubernetes Provisioner* would
be responsible for launching a kernel within its own Kubernetes pod,
communicating the kernel's connection information back to the
application (residing in a separate pod), and terminating the pod upon
the kernel's termination. In essence, a kernel provisioner is an
*abstraction layer* between the ``KernelManager`` and today's kernel
*process* (i.e., ``Popen``).

The kernel manager and kernel provisioner relationship
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prior to this enhancement, the only extension point for customizing a
kernel's behavior could occur by subclassing ``KernelManager``. This
proved to be a limitation because the Jupyter framework allows for a
single ``KernelManager`` class at any time. While applications could
introduce a ``KernelManager`` subclass of their own, that
``KernelManager`` was then tied directly to *that* application and
thereby not usable as a ``KernelManager`` in another application. As a
result, we consider the ``KernelManager`` class to be an
*application-owned entity* upon which application-specific behaviors can
be implemented.

Kernel provisioners, on the other hand, are contained within the
``KernelManager`` (i.e., a *has-a* relationship) and applications are
agnostic as to what *kind* of provisioner is in use other than what is
conveyed via the kernel's specification (kernelspec). All kernel
interactions still occur via the ``KernelManager`` and ``KernelClient``
classes within ``jupyter_client`` and potentially subclassed by the
application.

Kernel provisioners are not related in any way to the ``KernelManager``
instance that controls their lifecycle, nor do they have any affinity to
the application within which they are used. They merely provide a
vehicle by which authors can extend the landscape in which a kernel can
reside, while not side-effecting the application. That said, some kernel
provisioners may introduce requirements on the application. For example
(and completely hypothetically speaking), a ``SlurmProvisioner`` may
impose the constraint that the server (``jupyter_client``) resides on an
edge node of the Slurm cluster. These kinds of requirements can be
mitigated by leveraging applications like `Jupyter Kernel Gateway <https://github.com/jupyter/kernel_gateway>`_ or
`Jupyter Enterprise Gateway <https://github.com/jupyter/enterprise_gateway>`_
where the gateway server resides on the edge
node of (or within) the cluster, etc.

Discovery
~~~~~~~~~

Kernel provisioning does not alter today's kernel discovery mechanism
that utilizes well-known directories of ``kernel.json`` files. Instead,
it optionally extends the current ``metadata`` stanza within the
``kernel.json`` to include the specification of the kernel provisioner
name, along with an optional ``config`` stanza, consisting of
provisioner-specific configuration items. For example, a container-based
provisioner will likely need to specify the image name in this section.
The important point is that the content of this section is
provisioner-specific.

.. code:: JSON

      "metadata": {
        "kernel_provisioner": {
          "provisioner_name": "k8s-provisioner",
          "config": {
              "image_name": "my_docker_org/kernel:2.1.5",
              "max_cpus": 4
          }
        }
      },

Kernel provisioner authors implement their provisioners by deriving from
:class:`KernelProvisionerBase` and expose their provisioner for consumption
via entry-points:

.. code:: python

    'jupyter_client.kernel_provisioners': [
                'k8s-provisioner = my_package:K8sProvisioner',
            ],

Backwards Compatibility
~~~~~~~~~~~~~~~~~~~~~~~

Prior to this release, no ``kernel.json`` (kernelspec) will contain a
provisioner entry, yet the framework is now based on using provisioners.
As a result, when a ``kernel_provisioner`` stanza is **not** present in
a selected kernelspec, jupyter client will, by default, use the built-in
``LocalProvisioner`` implementation as its provisioner. This provisioner
retains today's local kernel functionality. It can also be subclassed
for those provisioner authors wanting to extend the functionality of
local kernels. The result of launching a kernel in this manner is
equivalent to the following stanza existing in the ``kernel.json`` file:

.. code:: JSON

      "metadata": {
        "kernel_provisioner": {
          "provisioner_name": "local-provisioner",
          "config": {
          }
        }
      },

Should a given installation wish to use a *different* provisioner as
their "default provisioner" (including subclasses of
``LocalProvisioner``), they can do so by specifying a value for
``KernelProvisionerFactory.default_provisioner_name``.

Implementing a custom provisioner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The impact of Kernel Provisioning is that it enables the ability to
implement custom kernel provisioners to manage a kernel's lifecycle
within any runtime environment. There are currently two approaches by
which that can be accomplished, extending the ``KernelProvisionerBase``
class or extending the built-in class - ``LocalProvisioner``. As more
provisioners are introduced, some may be implemented in an abstract
sense, from which specific implementations can be authored.

Extending ``LocalProvisioner``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you're interested in running kernels locally and yet adjust their
behavior, there's a good chance you can simply extend
``LocalProvisioner`` via subclassing. This amounts to deriving from
``LocalProvisioner`` and overriding appropriate methods to provide your
custom functionality.

In this example, RBACProvisioner will verify whether the current user is
in the role meant for this kernel by calling a method implemented within *this*
provisioner. If the user is not in the role, an exception will be thrown.

.. code:: python

    class RBACProvisioner(LocalProvisioner):

        role: str = Unicode(config=True)

        async def pre_launch(self, **kwargs: Any) -> Dict[str, Any]:

            if not self.user_in_role(self.role):
                raise PermissionError(f"User is not in role {self.role} and "
                                      f"cannot launch this kernel.")

            return await super().pre_launch(**kwargs)

It is important to note *when* it's necessary to call the superclass in
a given method - since the operations it performs may be critical to the
kernel's management. As a result, you'll likely need to become familiar
with how ``LocalProvisioner`` operates.

Extending ``KernelProvisionerBase``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you'd like to launch your kernel in an environment other than the
local server, then you will need to consider subclassing :class:`KernelProvisionerBase`
directly.  This will allow you to implement the various kernel process
controls relative to your target environment.  For instance, if you
wanted to have your kernel hosted in a Hadoop YARN cluster, you will
need to implement process-control methods like :meth:`poll` and :meth:`wait`
to use the YARN REST API.  Or, similarly, a Kubernetes-based provisioner
would need to implement the process-control methods using the Kubernetes client
API, etc.

By modeling the :class:`KernelProvisionerBase` methods after :class:`subprocess.Popen`
a natural mapping between today's kernel lifecycle management takes place.  This,
coupled with the ability to add configuration directly into the ``config:`` stanza
of the ``kernel_provisioner`` metadata, allows for things like endpoint address,
image names, namespaces, hosts lists, etc. to be specified relative to your
kernel provisioner implementation.

The ``kernel_id`` corresponding to the launched kernel and used by the
kernel manager is now available *prior* to the kernel's launch.  This
enables provisioners with a unique *key* they can use to discover and
control their kernel when launched into resource-managed clusters such
as Hadoop YARN or Kubernetes.

.. tip::
    Use ``kernel_id`` as a discovery mechanism from your provisioner!

Here's a prototyped implementation of a couple of the abstract methods
of :class:`KernelProvisionerBase` for use in an Hadoop YARN cluster to
help illustrate a provisioner's implementation.  Note that the built-in
implementation of :class:`LocalProvisioner` can also be used as a reference.

Notice the internal method ``_get_application_id()``.  This method is
what the provisioner uses to determine if the YARN application (i.e.,
the kernel) is still running within te cluster.  Although the provisioner
doesn't dictate the application id, the application id is
discovered via the application *name* which is a function of ``kernel_id``.

.. code:: python

    async def poll(self) -> Optional[int]:
        """Submitting a new kernel/app to YARN will take a while to be ACCEPTED.
        Thus application ID will probably not be available immediately for poll.
        So will regard the application as RUNNING when application ID still in
        ACCEPTED or SUBMITTED state.

        :return: None if the application's ID is available and state is
                 ACCEPTED/SUBMITTED/RUNNING. Otherwise 0.
        """
        result = 0
        if self._get_application_id():
            state = self._query_app_state_by_id(self.application_id)
            if state in YarnProvisioner.initial_states:
                result = None

        return result


    async def send_signal(self, signum):
        """Currently only support 0 as poll and other as kill.

        :param signum
        :return:
        """
        if signum == 0:
            return await self.poll()
        elif signum == signal.SIGKILL:
            return await self.kill()
        else:
            return await super().send_signal(signum)

Notice how in some cases we can compose provisioner methods to implement others.  For
example, since sending a signal number of 0 is tantamount to polling the process, we
go ahead and call :meth:`poll` to handle `signum` of 0 and :meth:`kill` to handle
`SIGKILL` requests.

Here we see how ``_get_application_id`` uses the ``kernel_id`` to acquire the application
id - which is the *primary id* for controlling YARN application lifecycles. Since startup
in resource-managed clusters can tend to take much longer than local kernels, you'll typically
need a polling or notification mechanism within your provisioner.  In addition, your
provisioner will be asked by the ``KernelManager`` what is an acceptable startup time.
This answer is implemented in the provisioner via the :meth:`get_shutdown_wait_time` method.

.. code:: python

    def _get_application_id(self, ignore_final_states: bool = False) -> str:

        if not self.application_id:
            app = self._query_app_by_name(self.kernel_id)
            state_condition = True
            if type(app) is dict:
                state = app.get('state')
                self.last_known_state = state

                if ignore_final_states:
                    state_condition = state not in YarnProvisioner.final_states

                if len(app.get('id', '')) > 0 and state_condition:
                    self.application_id = app['id']
                    self.log.info(f"ApplicationID: '{app['id']}' assigned for "
                                  f"KernelID: '{self.kernel_id}', state: {state}.")
            if not self.application_id:
                self.log.debug(f"ApplicationID not yet assigned for KernelID: "
                               f"'{self.kernel_id}' - retrying...")
        return self.application_id


    def get_shutdown_wait_time(self, recommended: Optional[float] = 5.0) -> float:

        if recommended < yarn_shutdown_wait_time:
            recommended = yarn_shutdown_wait_time
            self.log.debug(f"{type(self).__name__} shutdown wait time adjusted to "
                           f"{recommended} seconds.")

        return recommended

Registering your custom provisioner
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once your custom provisioner has been authored, it needs to be exposed
as an
`entry point <https://packaging.python.org/specifications/entry-points/>`_.
To do this add the following to your ``setup.py`` (or equivalent) in its
``entry_points`` stanza using the group name
``jupyter_client.kernel_provisioners``:

::

            'jupyter_client.kernel_provisioners': [
                'rbac-provisioner = acme.rbac.provisioner:RBACProvisioner',
            ],

where:

-  ``rbac-provisioner`` is the *name* of your provisioner and what will
   be referenced within the ``kernel.json`` file
-  ``acme.rbac.provisioner`` identifies the provisioner module name, and
-  ``RBACProvisioner`` is custom provisioner object name
   (implementation) that (directly or indirectly) derives from
   ``KernelProvisionerBase``

Deploying your custom provisioner
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The final step in getting your custom provisioner deployed is to add a
``kernel_provisioner`` stanza to the appropriate ``kernel.json`` files.
This can be accomplished manually or programmatically (in which some
tooling is implemented to create the appropriate ``kernel.json`` file).
In either case, the end result is the same - a ``kernel.json`` file with
the appropriate stanza within ``metadata``. The *vision* is that kernel
provisioner packages will include an application that creates kernel
specifications (i.e., ``kernel.json`` et. al.) pertaining to that
provisioner.

Following on the previous example of ``RBACProvisioner``, one would find
the following ``kernel.json`` file in directory
``/usr/local/share/jupyter/kernels/rbac_kernel``:

.. code:: JSON

    {
      "argv": ["python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
      "env": {},
      "display_name": "RBAC Kernel",
      "language": "python",
      "interrupt_mode": "signal",
      "metadata": {
        "kernel_provisioner": {
          "provisioner_name": "rbac-provisioner",
          "config": {
              "role": "data_scientist"
          }
        }
      }
    }

Listing available kernel provisioners
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To confirm that your custom provisioner is available for use,
the ``jupyter kernelspec`` command has been extended to include
a `provisioners` sub-command.  As a result, running ``jupyter kernelspec provisioners``
will list the available provisioners by name followed by their module and object
names (colon-separated):

.. code:: bash

    $ jupyter kernelspec provisioners

    Available kernel provisioners:
      local-provisioner    jupyter_client.provisioning:LocalProvisioner
      rbac-provisioner     acme.rbac.provisioner:RBACProvisioner
