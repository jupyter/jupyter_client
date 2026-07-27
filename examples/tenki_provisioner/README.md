# Tenki Sandbox kernel provisioner

Run Jupyter kernels inside disposable [Tenki Sandbox](https://tenki.cloud/docs/sandbox)
microVMs, using the [`jupyter_client` kernel provisioner](https://jupyter-client.readthedocs.io/en/latest/provisioning.html)
extension point.

Every kernel you start is launched in its own isolated Linux microVM instead of
on your machine. Notebook code — including anything an AI agent generates — runs
fully sandboxed, with its own CPU/memory and no access to your local filesystem.
When the kernel shuts down, the microVM is destroyed.

This example is built **entirely on the [`tenki-sandbox` Python SDK](https://pypi.org/project/tenki-sandbox/)** —
no SSH, no CLI, and no inbound networking required.

## How it works

A Jupyter kernel exposes five ZeroMQ channels (`shell`, `iopub`, `stdin`,
`control`, `hb`). Normally these are TCP ports on `localhost`. Because the kernel
here runs inside a microVM, we instead drive it over ZeroMQ's **`ipc` transport**,
so each channel is a Unix-domain socket the kernel *binds* inside the guest.

`jupyter_client` runs locally, so it needs sockets to *connect* to locally. The
provisioner writes two connection files that are identical except for the socket
path prefix — one for the client (a private temp dir) and one for the kernel
(under the guest's `/home/tenki`) — so the HMAC signing key and channel indices
line up on both ends. It then bridges each local socket to the matching guest
socket with the SDK's `dial` primitive, a raw bidirectional byte stream into the
microVM:

```
 jupyter_client                 TenkiProvisioner                    microVM
 ┌────────────┐   ipc:// unix   ┌──────────────────┐  sandbox.dial  ┌──────────┐
 │ KernelClient├───────────────►│ local socket ↔   ├───────────────►│ ipykernel│
 │  (5 ZMQ     │◄───────────────┤ dial() bridge    │◄───────────────┤ (5 ipc   │
 │   channels) │                │ (one per channel)│  gRPC stream   │  sockets)│
 └────────────┘                 └──────────────────┘                └──────────┘
```

Lifecycle mapping onto `KernelProvisionerBase`:

| Provisioner method | Tenki action                                                   |
| ------------------ | -------------------------------------------------------------- |
| `pre_launch`       | Switch kernel to `ipc`; stage local + guest connection files   |
| `launch_kernel`    | `Sandbox.create` → install `ipykernel` → `start` kernel → bridge sockets |
| `poll` / `wait`    | Track the guest process via the SDK `Process` handle           |
| `send_signal`      | Forward the signal to the guest process (`SIGINT` interrupts)  |
| `kill` / `terminate` | Signal the guest process                                     |
| `cleanup`          | Close the socket bridge and terminate the microVM              |

## Install

```bash
pip install -e .            # from this directory
# or, once published:
# pip install tenki-jupyter-provisioner
```

This registers the provisioner under the name `tenki-provisioner` via the
`jupyter_client.kernel_provisioners` entry point. Confirm it:

```bash
jupyter kernelspec provisioners
#   tenki-provisioner    tenki_provisioner:TenkiProvisioner
```

## Authenticate

Get an API key from your Tenki workspace settings and export it (the SDK reads
it automatically):

```bash
export TENKI_API_KEY=tk_...
```

You can also pass `auth_token` / `base_url` in the kernelspec `config` stanza.

Some deployments require you to name the **project** the sandbox is created in
(the Python SDK does not auto-select one). Discover the ids with:

```python
from tenki_sandbox import Client

for ws in Client().who_am_i().workspaces:
    print(ws.name, ws.id)
    for p in ws.projects:
        print("  ", p.name, p.id)
```

Then set `project_id` (and optionally `workspace_id`) in the kernelspec config.

## Use it

Install a kernelspec that routes through the provisioner:

```bash
python -m tenki_provisioner.kernelspec install \
    --name tenki-python --display-name "Python (Tenki Sandbox)" \
    --cpu 4 --memory-mb 8192
```

Now `Python (Tenki Sandbox)` appears in Jupyter Lab/Notebook, and
`jupyter console --kernel tenki-python` opens a shell whose kernel lives in a
microVM. A sample `kernel.json` is in [`kernels/tenki_python/`](kernels/tenki_python/kernel.json).

### Configuration

Set these in the kernelspec `metadata.kernel_provisioner.config` stanza (or as
traitlets):

| Option                 | Default     | Description                                       |
| ---------------------- | ----------- | ------------------------------------------------- |
| `cpu_cores`            | `2`         | vCPUs for the microVM (1–16)                      |
| `memory_mb`            | `4096`      | Memory in MiB                                      |
| `project_id`           | `""`        | Tenki project to create the sandbox in (may be required) |
| `workspace_id`         | `""`        | Tenki workspace id (optional)                     |
| `image`                | service default | Sandbox image reference                       |
| `allow_outbound`       | `true`      | Guest outbound network (needed to pip install)    |
| `idle_timeout_minutes` | `0`         | Idle pause/terminate after N minutes (0 = default)|
| `max_duration_seconds` | `3600`      | Hard lifetime cap / leak backstop (0 = no cap; raise for long sessions) |
| `install_ipykernel`    | `true`      | `pip install ipykernel` in the guest if missing   |
| `extra_pip_packages`   | `[]`        | Extra packages to install in the guest            |
| `kernel_argv`          | ipykernel   | Guest launch command; `{connection_file}` is substituted |
| `env`                  | `{}`        | Environment variables for the kernel process      |

## Requirements & limitations

- **Unix client only.** The `ipc` transport uses Unix-domain sockets, so the
  machine running `jupyter_client` must be Linux or macOS. (The kernel always
  runs on Linux inside the microVM.)
- The guest image must have a Python interpreter; `ipykernel` is installed on
  first launch unless you bake it into the image (`install_ipykernel=false`).
  The default image (Ubuntu 24.04 / Python 3.12) marks its system interpreter
  externally-managed (PEP 668); the provisioner handles this by retrying the
  install with `--break-system-packages` (the guest is disposable).
- **Restart** provisions a fresh microVM — kernel restarts do not preserve guest
  state.

## Lifecycle & duration notes

- **Leak-safe launch.** If provisioning succeeds but a later step fails (or the
  launch is cancelled), the microVM is torn down before the error propagates. As
  a last resort, set `max_duration_seconds` so an orphaned VM self-terminates.
- **Idle sessions.** A kernel is idle between cells. If your deployment
  idle-pauses sandboxes and the gap exceeds the idle window, the VM can pause
  mid-session. `tenki-sandbox` 0.4.0 exposes no client-side activity API to
  refresh the idle timer (`refresh()` only reads state), so the provisioner does
  not attempt a keepalive. If you expect long idle gaps, raise (or disable via
  the service) `idle_timeout_minutes`.
- **Long-running cells.** `create_timeout` bounds *provisioning* only, not cell
  execution. There is no hard cell timeout; size `max_duration_seconds` to your
  longest expected session (it defaults to 1 hour as a leak backstop; `0`
  disables the cap).
- **Teardown is observable.** Terminating the microVM is retried a few times; if
  it still fails, `cleanup` raises rather than reporting a successful, leaked VM.
- **No cross-process reattach.** `get_provisioner_info`/`load_provisioner_info`
  are left at the base implementation; a provisioner in a different process
  cannot resume management of a running kernel.

## Tests

```bash
pip install -e ".[test]"
pytest
```

The unit tests mock the SDK. For a live end-to-end run (`TENKI_API_KEY` set),
see [`tests/README.md`](tests/README.md).
