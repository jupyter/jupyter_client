# Migration Guide

## Jupyter Client 8.0 to 9.0

Overall changes: removed direct usages of `tornado` in favor of `asyncio` loops.
We are still using `zmq.eventloop.zmqstream.ZMQStream`, which uses `tornado`
loops internally.

### API Changes

The following `loop` properties are now asyncio loops:

- `jupyter_client.ioloop.manager.IOLoopKernelManager.loop`
- `jupyter_client.ioloop.manager.AsyncIOLoopKernelManager.loop`
- `jupyter_client.ioloop.restarter.IOLoopKernelRestarter.loop`
- `jupyter_client.ioloop.restarter.AsyncIOLoopKernelRestarter.loop`
- `jupyter_client.threaded.ThreadedZMQSocketChannel.loop`
- `jupyter_client.threaded.IOLoopThread.ioloop`
- `jupyter_client.threaded.ThreadedKernelClient.ioloop`

The `jupyter_client.kernelapp.KernelApp` class now subclasses
`jupyter_core.application.JupyterAsyncApp`, and  performs its initialization
from within an asyncio loop.

The following function was added as a shim to the `jupyter_core` utility:

- `jupyter_client.utils.ensure_event_loop`

## Jupyter Client 7.0 to 8.0

The main goal of this release was to improve handling of asyncio and remove
the need for `nest_asyncio`.

### API Changes

- `jupyter_client.asynchronous.client.AsyncKernelClient.context` is now a `zmq.asyncio.Context`
- `jupyter_client.asynchronous.client.AsyncKernelClient.*_channel_class` are now instances of `jupyter_client.channels.AsyncZMQSocketChannel`

## Jupyter Client 6.0 to 7.0

### API Changes

All of the API changes for `KernelManager` and `AsyncKernelManager` in the 7.0 release were confined to _internal public_ methods, which we define as methods called from the _formally public_ methods but could be overridden in subclass implementations. As a result, these changes may impact subclasses of `KernelManager` or `AsyncKernelManager` provided those implementations also implement or call these methods, but should not affect applications that call only the _formally public_ methods.

#### `KernelManager`

The following internal methods had signature changes:

- `def pre_start_kernel(self, **kwargs) -> Tuple[List[str], Dict[str, Any]]:`

  - `pre_start_kernel` now returns a tuple consisting of the formatted kernel startup list and an updated set of keyword arguments.

- `def _launch_kernel(self, kernel_cmd: List[str], **kw) -> None:`

  - `_launch_kernel` now returns `None` instead of the `Popen` instance

- These methods now take the keyword argument `restart` indicating the shutdown was on behalf of a kernel restart (when `True`).

  - `def finish_shutdown(self, restart: bool = False):`
  - `def _kill_kernel(self, restart: bool = False):`
  - `def _send_kernel_sigterm(self, restart: bool = False):`

- Attribute `kernel` has been removed and _logically_ replaced with `provisioner` - which is an instance of `KernelProvisionerBase` and can be viewed as an abstract `Popen` instance.

#### `AsyncKernelManager`

Besides the signature and attribute changes described above, the following internal methods were made `async` for `AsyncKernelManager`:

- `async def pre_start_kernel(self, **kwargs) -> Tuple[List[str], Dict[str, Any]]:`
- `async def post_start_kernel(self, **kwargs):`
- `async def request_shutdown(self, restart: bool = False):`
- `async def cleanup_resources(self, restart: bool = False):`

#### `AsyncKernelClient`

We dropped the `block: bool = True` keyword argument for the following methods:

- `async def get_shell_msg(self, timeout: Optional[float] = None) -> Dict[str, Any]:`
- `async def get_iopub_msg(self, timeout: Optional[float] = None) -> Dict[str, Any]:`
- `async def get_stdin_msg(self, timeout: Optional[float] = None) -> Dict[str, Any]:`
- `async def get_control_msg(self, timeout: Optional[float] = None) -> Dict[str, Any]:`

Calling these methods with `block=False` previously translates to calling them with `timeout=0` now.
Calling these methods with `block=True` previously translates to calling them with a non-zero `timeout` value now.

#### `BlockingKernelClient`

We dropped the `block: bool = True` keyword argument for the following methods:

- `def get_shell_msg(self, timeout: Optional[float] = None) -> Dict[str, Any]:`
- `def get_iopub_msg(self, timeout: Optional[float] = None) -> Dict[str, Any]:`
- `def get_stdin_msg(self, timeout: Optional[float] = None) -> Dict[str, Any]:`
- `def get_control_msg(self, timeout: Optional[float] = None) -> Dict[str, Any]:`

Calling these methods with `block=False` previously translates to calling them with `timeout=0` now.
Calling these methods with `block=True` previously translates to calling them with a non-zero `timeout` value now.

#### `BlockingKernelClient`

#### `ZMQSocketChannel`

We dropped the `block: bool = True` keyword argument for the following method:

- `async def get_msg(self, timeout: Optional[float] = None) -> Dict[str, Any]:`:

Calling this method with `block=False` previously translates to calling it with `timeout=0` now.
Calling this method with `block=True` previously translates to calling it with a non-zero `timeout` value now.

```{admonition} Note
Prefer calling e.g. `client.get_shell_msg()` over `client.shell_channel.get_msg()`.
```

### Deprecations removed

#### Method `KernelManager.cleanup()`

The `cleanup()` method on `KernelManager` has been removed. `cleanup_resources(restart: bool = False)` should be used.

#### Attribute `KernelManager.kernel_cmd`

This attribute had been marked for deprecation for 4 years. The command used to start the kernel is derived from the `argv` stanza of the kernel specification file (`kernel.json`).
