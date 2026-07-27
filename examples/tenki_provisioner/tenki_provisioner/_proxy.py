"""A tiny loopback proxy that bridges local Unix-domain sockets to Unix sockets
inside a Tenki Sandbox using the SDK's ``dial`` primitive.

A Jupyter kernel speaks over five ZeroMQ channels.  When the kernel runs inside
a Tenki Sandbox microVM we run it over the ZeroMQ ``ipc`` transport, so each
channel is a Unix-domain socket the kernel *binds* inside the guest.  The client
(``jupyter_client``) is local, so it needs something to *connect* to locally.

For every channel we bind a local Unix socket and, whenever the local ZeroMQ
client connects, we open a ``dial`` stream to the matching guest socket and pump
bytes in both directions.  ``dial`` is a bidirectional, raw byte stream provided
by the Tenki Sandbox SDK -- no external tooling (ssh, CLI) is required.
"""

from __future__ import annotations

import logging
import os
import socket
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tenki_sandbox import Sandbox

_BUFSIZE = 65536


def _safe(fn) -> None:
    try:
        fn()
    except Exception:  # best-effort teardown
        pass


class IpcSocketProxy:
    """Bridge ``local_path`` <-> ``remote_path`` for a set of channel sockets.

    Parameters
    ----------
    sandbox:
        A live :class:`tenki_sandbox.Sandbox` whose ``dial`` method opens a raw
        stream to a Unix socket inside the guest.
    mappings:
        Pairs of ``(local_socket_path, remote_socket_path)`` -- one per Jupyter
        channel.
    """

    def __init__(
        self,
        sandbox: Sandbox,
        mappings: list[tuple[str, str]],
        log: logging.Logger | None = None,
    ) -> None:
        self._sandbox = sandbox
        self._mappings = mappings
        self._log = log or logging.getLogger(__name__)
        self._servers: list[socket.socket] = []
        self._threads: list[threading.Thread] = []
        self._conns: list[tuple[socket.socket, object]] = []
        self._lock = threading.Lock()
        self._closed = False

    def start(self) -> None:
        """Bind every local socket and begin accepting connections."""
        for local_path, remote_path in self._mappings:
            _safe(lambda p=local_path: os.unlink(p) if os.path.exists(p) else None)
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(local_path)
            server.listen(16)
            self._servers.append(server)
            t = threading.Thread(
                target=self._accept_loop,
                args=(server, remote_path),
                name=f"tenki-ipc-accept:{os.path.basename(local_path)}",
                daemon=True,
            )
            t.start()
            self._threads.append(t)
        self._log.debug("IPC proxy started with %d channel(s)", len(self._mappings))

    def _accept_loop(self, server: socket.socket, remote_path: str) -> None:
        while not self._closed:
            try:
                conn, _ = server.accept()
            except OSError:
                return  # server socket closed during shutdown
            t = threading.Thread(target=self._handle, args=(conn, remote_path), daemon=True)
            t.start()

    def _handle(self, conn: socket.socket, remote_path: str) -> None:
        try:
            dial = self._sandbox.dial(remote_path)
        except Exception as exc:  # kernel socket may not be up yet
            self._log.debug("dial(%s) failed: %s", remote_path, exc)
            _safe(conn.close)
            return

        with self._lock:
            if self._closed:
                _safe(conn.close)
                _safe(dial.close)
                return
            self._conns.append((conn, dial))

        def sock_to_dial() -> None:
            try:
                while True:
                    data = conn.recv(_BUFSIZE)
                    if not data:
                        break
                    dial.write(data)
            except Exception:
                pass
            finally:
                _safe(dial.close)  # half-close write side toward the guest

        def dial_to_sock() -> None:
            try:
                while True:
                    data = dial.read(_BUFSIZE)
                    if not data:
                        break
                    conn.sendall(data)
            except Exception:
                pass
            finally:
                _safe(lambda: conn.shutdown(socket.SHUT_WR))

        threading.Thread(target=sock_to_dial, daemon=True).start()
        threading.Thread(target=dial_to_sock, daemon=True).start()

    def close(self) -> None:
        """Stop accepting and tear down every open connection."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            conns = list(self._conns)
            self._conns.clear()
        for server in self._servers:
            _safe(server.close)
        for conn, dial in conns:
            _safe(conn.close)
            _safe(dial.close)
        for local_path, _ in self._mappings:
            _safe(lambda p=local_path: os.unlink(p) if os.path.exists(p) else None)
        self._log.debug("IPC proxy closed")
