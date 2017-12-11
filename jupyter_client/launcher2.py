"""Machinery for launching a kernel locally.

Used by jupyter_client.manager2.
"""
from binascii import b2a_hex
import errno
import json
import os
import re
import six
import socket
import stat
from subprocess import PIPE
import sys
import warnings

from ipython_genutils.encoding import getdefaultencoding
from ipython_genutils.py3compat import cast_bytes_py2
from jupyter_core.paths import jupyter_runtime_dir
from jupyter_core.utils import ensure_dir_exists
from .localinterfaces import localhost

def new_key():
    """Generate a new random key string.

    Avoids problematic runtime import in stdlib uuid on Python 2.

    Returns
    -------

    id string (16 random bytes as hex-encoded text, chunks separated by '-')
    """
    buf = os.urandom(16)
    return u'-'.join(b2a_hex(x).decode('ascii') for x in (
        buf[:4], buf[4:]
    ))

def random_ports(ip, transport='tcp'):
    """Pick a set of random, unused ports for the kernel to use.
    """
    res = {}
    port_names = ['shell_port', 'iopub_port', 'stdin_port', 'control_port',
                  'hb_port']
    if transport == 'tcp':
        # store sockets temporarily to avoid reusing a port number
        tmp_socks = []
        for _ in port_names:
            sock = socket.socket()
            # struct.pack('ii', (0,0)) is 8 null bytes
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b'\0' * 8)
            sock.bind((ip, 0))
            tmp_socks.append(sock)
        for name, sock in zip(port_names, tmp_socks):
            port = sock.getsockname()[1]
            sock.close()
            res[name] = port
    else:
        N = 1
        for name in port_names:
            while os.path.exists("%s-%s" % (ip, str(N))):
                N += 1
            res[name] = N
            N += 1
    return res

def set_sticky_bit(fname):
    """Set the sticky bit on the file and its parent directory.

    This stops it being deleted by periodic cleanup of XDG_RUNTIME_DIR.
    """
    if not hasattr(stat, 'S_ISVTX'):
        return

    paths = [fname]
    runtime_dir = os.path.dirname(fname)
    if runtime_dir:
        paths.append(runtime_dir)
    for path in paths:
        permissions = os.stat(path).st_mode
        new_permissions = permissions | stat.S_ISVTX
        if new_permissions != permissions:
            try:
                os.chmod(path, new_permissions)
            except OSError as e:
                if e.errno == errno.EPERM and path == runtime_dir:
                    # suppress permission errors setting sticky bit on runtime_dir,
                    # which we may not own.
                    pass
                else:
                    # failed to set sticky bit, probably not a big deal
                    warnings.warn(
                        "Failed to set sticky bit on %r: %s"
                        "\nProbably not a big deal, but runtime files may be cleaned up periodically." % (path, e),
                        RuntimeWarning,
                    )

def make_connection_file(ip=None, transport='tcp'):
    """Generates a JSON config file, including the selection of random ports.

    Parameters
    ----------

    ip  : str, optional
        The ip address the kernel will bind to.

    transport : str, optional
        The ZMQ transport to use: tcp or ipc
    """
    if not ip:
        ip = localhost()

    runtime_dir = jupyter_runtime_dir()
    ensure_dir_exists(runtime_dir)
    fname = os.path.join(runtime_dir, 'kernel-%s.json' % new_key())

    cfg = random_ports(ip=ip, transport=transport)
    cfg['ip'] = ip
    cfg['key'] = new_key()
    cfg['transport'] = transport
    cfg['signature_scheme'] = 'hmac-sha256'

    with open(fname, 'w') as f:
        f.write(json.dumps(cfg, indent=2))

    set_sticky_bit(fname)

    return fname, cfg

def format_kernel_cmd(cmd, connection_file, kernel_resource_dir=None):
    """Replace templated args (e.g. {connection_file})
    """
    if cmd and cmd[0] == 'python':
        # executable is 'python', use sys.executable.
        # These will typically be the same,
        # but if the current process is in an env
        # and has been launched by abspath without
        # activating the env, python on PATH may not be sys.executable,
        # but it should be.
        cmd[0] = sys.executable

    ns = dict(connection_file=connection_file,
              prefix=sys.prefix,
             )

    if kernel_resource_dir:
        ns["resource_dir"] = kernel_resource_dir

    pat = re.compile(r'\{([A-Za-z0-9_]+)\}')
    def from_ns(match):
        """Get the key out of ns if it's there, otherwise no change."""
        return ns.get(match.group(1), match.group())

    return [ pat.sub(from_ns, arg) for arg in cmd ]

def build_popen_kwargs(cmd_template, connection_file, extra_env=None, cwd=None):
    """Build a dictionary of arguments to pass to Popen"""
    kwargs = {}
    # Popen will fail (sometimes with a deadlock) if stdin, stdout, and stderr
    # are invalid. Unfortunately, there is in general no way to detect whether
    # they are valid.  The following two blocks redirect them to (temporary)
    # pipes in certain important cases.

    # If this process has been backgrounded, our stdin is invalid. Since there
    # is no compelling reason for the kernel to inherit our stdin anyway, we'll
    # place this one safe and always redirect.
    kwargs['stdin'] = PIPE

    # If this process in running on pythonw, we know that stdin, stdout, and
    # stderr are all invalid.
    redirect_out = sys.executable.endswith('pythonw.exe')
    if redirect_out:
        kwargs['stdout'] = kwargs['stderr'] = open(os.devnull, 'w')

    cmd = format_kernel_cmd(cmd_template, connection_file)

    kwargs['env'] = env = os.environ.copy()
    # Don't allow PYTHONEXECUTABLE to be passed to kernel process.
    # If set, it can bork all the things.
    env.pop('PYTHONEXECUTABLE', None)

    if extra_env:
        print(extra_env)
        env.update(extra_env)

    # TODO: where is this used?
    independent = False

    if sys.platform == 'win32':
        # Popen on Python 2 on Windows cannot handle unicode args or cwd
        encoding = getdefaultencoding(prefer_stream=False)
        kwargs['args'] = [cast_bytes_py2(c, encoding) for c in cmd]
        if cwd:
            kwargs['cwd'] = cast_bytes_py2(cwd,
                                 sys.getfilesystemencoding() or 'ascii')

        try:
            # noinspection PyUnresolvedReferences
            from _winapi import DuplicateHandle, GetCurrentProcess, \
                DUPLICATE_SAME_ACCESS, CREATE_NEW_PROCESS_GROUP
        except:
            # noinspection PyUnresolvedReferences
            from _subprocess import DuplicateHandle, GetCurrentProcess, \
                DUPLICATE_SAME_ACCESS, CREATE_NEW_PROCESS_GROUP
        # Launch the kernel process
        if independent:
            kwargs['creationflags'] = CREATE_NEW_PROCESS_GROUP
        else:
            pid = GetCurrentProcess()
            handle = DuplicateHandle(pid, pid, pid, 0,
                                     True,  # Inheritable by new processes.
                                     DUPLICATE_SAME_ACCESS)
            env['JPY_PARENT_PID'] = str(int(handle))

    else:
        kwargs['args'] = cmd
        kwargs['cwd'] = cwd
        # Create a new session.
        # This makes it easier to interrupt the kernel,
        # because we want to interrupt the whole process group.
        # We don't use setpgrp, which is known to cause problems for kernels starting
        # certain interactive subprocesses, such as bash -i.
        if six.PY3:
            kwargs['start_new_session'] = True
        else:
            kwargs['preexec_fn'] = lambda: os.setsid()
        if not independent:
            env['JPY_PARENT_PID'] = str(os.getpid())

    return kwargs

def prepare_interrupt_event(env, interrupt_event=None):
    if sys.platform == 'win32':
        from .win_interrupt import create_interrupt_event
        # Create a Win32 event for interrupting the kernel
        # and store it in an environment variable.
        if interrupt_event is None:
            interrupt_event = create_interrupt_event()
        env["JPY_INTERRUPT_EVENT"] = str(interrupt_event)
        # deprecated old env name:
        env["IPY_INTERRUPT_EVENT"] = env["JPY_INTERRUPT_EVENT"]
        return interrupt_event
