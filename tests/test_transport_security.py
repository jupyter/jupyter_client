"""Tests for the ZMQ transport security."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import json
from unittest.mock import patch

import pytest
import zmq
from traitlets import TraitError

from jupyter_client import KernelManager
from jupyter_client.channels import HBChannel
from jupyter_client.client import KernelClient
from jupyter_client.connect import ConnectionFileMixin
from jupyter_client.kernelspec import KernelSpec, KernelSpecManager
from jupyter_client.session import Session


@pytest.mark.parametrize(
    "transport_encryption",
    [
        "disabled",
        "auto",
        "required",
    ],
)
def test_iopub_plaintext_visibility_depends_on_curve(transport_encryption, tmp_path):
    """An unauthenticated subscriber sees plaintext only when Curve is disabled."""

    kernel_name = "curve-test"
    kernels_dir = tmp_path / "kernels"
    kernel_dir = kernels_dir / kernel_name
    kernel_dir.mkdir(parents=True)
    with (kernel_dir / "kernel.json").open("w") as f:
        json.dump(
            {
                "argv": ["python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": "curve-test",
                "language": "python",
                "metadata": {"supported_encryption": "curve"},
            },
            f,
        )

    km = KernelManager(
        connection_file=str(tmp_path / "kernel.json"),
        kernel_name=kernel_name,
        kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels_dir)]),
    )
    km.cache_ports = False
    km.transport_encryption = transport_encryption
    km.pre_start_kernel()

    session = Session(key=b"secret-hmac-key")
    server = km.context.socket(zmq.XPUB)
    eavesdropper_sock = km.context.socket(zmq.SUB)
    eavesdropper_sock.setsockopt(zmq.SUBSCRIBE, b"")

    expect_plaintext_visible = transport_encryption == "disabled"

    server_info = km.get_connection_info()
    if "curve_publickey" in server_info and "curve_secretkey" in server_info:
        server.curve_secretkey = server_info["curve_secretkey"].encode()
        server.curve_publickey = server_info["curve_publickey"].encode()
        server.curve_server = True

    try:
        server.bind(f"tcp://{km.ip}:{km.iopub_port}")

        # Eavesdropper connects with no authentication or curve keys.
        eavesdropper_sock.connect(f"tcp://{km.ip}:{km.iopub_port}")

        # In non-Curve mode, XPUB receives the subscription and we drain it.
        # In Curve mode, unauthenticated peers are rejected so no event arrives.
        sub_poller = zmq.Poller()
        sub_poller.register(server, zmq.POLLIN)
        sub_events = dict(sub_poller.poll(timeout=1000))
        if server in sub_events:
            server.recv()  # discard subscription frame

        # Simulate a kernel publishing stream messages via Session
        # (HMAC-signed, but not encrypted at the transport layer).
        sensitive_content = {"name": "stdout", "text": "top_secret_output_12345"}
        session.send(server, "stream", sensitive_content, ident=b"kernel.stream.stdout")

        # Check if an unauthenticated subscriber can read plaintext payload,
        # using the same event polling behavior in both modes.
        recv_poller = zmq.Poller()
        recv_poller.register(eavesdropper_sock, zmq.POLLIN)
        events = dict(recv_poller.poll(timeout=1000))

        did_receive = eavesdropper_sock in events
        assert did_receive is expect_plaintext_visible, (
            "Unexpected unauthenticated visibility result for IOPub payload"
        )
        if expect_plaintext_visible:
            # Demonstrates that the message content is visible in plaintext frames when Curve is disabled.
            raw_frames = eavesdropper_sock.recv_multipart()
            raw_bytes = b"".join(raw_frames)
            assert b"top_secret_output_12345" in raw_bytes, (
                f"Expected plaintext content in raw frames.\nRaw bytes: {raw_bytes!r}"
            )
            assert b"stream" in raw_bytes, "msg_type 'stream' should be visible in plaintext frames"

    finally:
        server.close(linger=0)
        eavesdropper_sock.close(linger=0)
        km.cleanup_connection_file()
        km.context.term()


@pytest.mark.parametrize("value", ["auto", "required"])
def test_transport_encryption_raises_when_curve_unavailable(value):
    """Setting transport_encryption to 'auto' or 'required' raises TraitError when CurveZMQ is unavailable."""
    with (
        patch("zmq.has", return_value=False),
        pytest.raises(TraitError, match=r"zmq\.has\('curve'\)"),
    ):
        KernelManager(transport_encryption=value)


@pytest.mark.parametrize("value", ["auto", "required"])
def test_transport_encryption_accepted_when_curve_available(value):
    """Setting transport_encryption to 'auto' or 'required' is accepted when CurveZMQ is available."""
    with patch("zmq.has", return_value=True):
        km = KernelManager(transport_encryption=value)
        assert km.transport_encryption == value


def test_transport_encryption_disabled_does_not_require_curve():
    """Setting transport_encryption to 'disabled' never raises regardless of CurveZMQ availability."""
    with patch("zmq.has", return_value=False):
        km = KernelManager(transport_encryption="disabled")
        assert km.transport_encryption == "disabled"


def _make_km(tmp_path, *, supported_encryption, transport_encryption):
    """Helper: build a KernelManager with a kernelspec whose metadata is set directly."""
    metadata = (
        {} if supported_encryption is None else {"supported_encryption": supported_encryption}
    )
    km = KernelManager(connection_file=str(tmp_path / "kernel.json"))
    km._kernel_spec = KernelSpec(
        resource_dir="test",
        argv=["python", "-c", "pass"],
        display_name="test_kernel",
        language="python",
        metadata=metadata,
    )
    km.cache_ports = False
    km.transport_encryption = transport_encryption
    return km


def test_enabled_without_curve_kernelspec_skips_keys(tmp_path):
    """transport_encryption='auto' skips key provisioning when kernelspec lacks curve support."""
    km = _make_km(tmp_path, supported_encryption=None, transport_encryption="auto")
    km.pre_start_kernel()
    info = km.get_connection_info()
    assert "curve_publickey" not in info
    assert "curve_secretkey" not in info
    km.cleanup_connection_file()
    km.context.term()


def test_enabled_with_curve_kernelspec_provisions_keys(tmp_path):
    """transport_encryption='auto' provisions keys when kernelspec declares curve support."""
    km = _make_km(tmp_path, supported_encryption="curve", transport_encryption="auto")
    km.pre_start_kernel()
    info = km.get_connection_info()
    assert "curve_publickey" in info
    assert "curve_secretkey" in info
    km.cleanup_connection_file()
    km.context.term()


def test_required_without_curve_kernelspec_raises(tmp_path):
    """transport_encryption='required' raises RuntimeError when kernelspec lacks curve support."""
    km = _make_km(tmp_path, supported_encryption=None, transport_encryption="required")
    with pytest.raises(RuntimeError, match=r"metadata\.supported_encryption"):
        km.pre_start_kernel()
    km.context.term()


def test_curve_keys_reused_across_restart(tmp_path):
    """Curve keys are preserved (not regenerated) on restart, consistent with
    how session.key is handled. Both keys live in the same file, protect the
    same local connection, and there is no security reason to rotate one but
    not the other. Regenerating caused a key mismatch: the manager held new
    keys while the connection file (guarded from rewrite) still had the old
    ones, breaking every post-restart nudge.
    """
    km = _make_km(tmp_path, supported_encryption="curve", transport_encryption="required")
    km.pre_start_kernel()

    initial_pubkey = km.curve_publickey
    assert initial_pubkey is not None
    with open(km.connection_file) as f:
        assert json.load(f)["curve_publickey"] == initial_pubkey.decode("ascii")

    # Reproduce the restart sequence: cleanup (file preserved) then re-start.
    km.cleanup_resources(restart=True)
    km.pre_start_kernel()

    restarted_pubkey = km.curve_publickey
    assert restarted_pubkey == initial_pubkey, "Curve keys must be reused across restart"

    with open(km.connection_file) as f:
        restarted_info = json.load(f)

    assert restarted_info["curve_publickey"] == restarted_pubkey.decode("ascii")

    km.cleanup_connection_file()
    km.context.term()


def test_connect_shell_to_curve_server_with_curve_keys_succeeds():
    """Public API path: load_connection_info + connect_shell works with curve keys."""
    pub, sec = zmq.curve_keypair()

    # Set up a CurveZMQ server socket (simulating the kernel side).
    ctx = zmq.Context()
    server = ctx.socket(zmq.ROUTER)
    server.curve_secretkey = sec
    server.curve_publickey = pub
    server.curve_server = True
    port = server.bind_to_random_port("tcp://127.0.0.1")

    try:
        # Configure through the same public parsing path used for
        # connection-file content.
        info = {
            "ip": "127.0.0.1",
            "transport": "tcp",
            "shell_port": port,
            "key": "abc123",
            "signature_scheme": "hmac-sha256",
            "curve_publickey": pub.decode("ascii"),
            "curve_secretkey": sec.decode("ascii"),
        }
        mixin = ConnectionFileMixin()
        mixin.context = ctx
        mixin.load_connection_info(info)

        client_sock = mixin.connect_shell()
        try:
            client_sock.send(b"probe", flags=zmq.NOBLOCK)

            poller = zmq.Poller()
            poller.register(server, zmq.POLLIN)
            events = dict(poller.poll(timeout=1000))
            assert server in events, (
                "Authenticated client message was not received - "
                "connect_shell() did not produce a working Curve-authenticated socket"
            )
        finally:
            client_sock.close(linger=0)
    finally:
        server.close(linger=0)
        ctx.term()


def test_hb_channel_class_without_curve_support_raises_when_curve_is_active():
    """KernelClient.hb_channel raises RuntimeError when the hb_channel_class
    does not accept curve_serverkey but CurveZMQ is active."""

    class LegacyHBChannel(HBChannel):
        """Simulates an old heartbeat channel class that predates curve support."""

        def __init__(self, context, session, address):  # type: ignore[override]
            super().__init__(context, session, address)

    pub, _sec = zmq.curve_keypair()

    client = KernelClient()
    client.hb_channel_class = LegacyHBChannel  # type: ignore[assignment]
    client.load_connection_info(
        {
            "ip": "127.0.0.1",
            "transport": "tcp",
            "hb_port": 5555,
            "key": "abc123",
            "signature_scheme": "hmac-sha256",
            "curve_publickey": pub.decode("ascii"),
            "curve_secretkey": pub.decode("ascii"),
        }
    )

    try:
        with pytest.raises(RuntimeError, match=r"LegacyHBChannel.*curve_serverkey"):
            _ = client.hb_channel
    finally:
        client.context.term()


def test_hb_channel_class_without_curve_support_does_not_raise_when_curve_disabled():
    """KernelClient.hb_channel remains usable with legacy hb_channel_class when Curve is off."""

    class LegacyHBChannel(HBChannel):
        """Simulates an old heartbeat channel class that predates curve support."""

        def __init__(self, context, session, address):  # type: ignore[override]
            super().__init__(context, session, address)

    client = KernelClient()
    client.hb_channel_class = LegacyHBChannel  # type: ignore[assignment]
    client.load_connection_info(
        {
            "ip": "127.0.0.1",
            "transport": "tcp",
            "hb_port": 5555,
            "key": "abc123",
            "signature_scheme": "hmac-sha256",
        }
    )

    try:
        hb = client.hb_channel
        assert isinstance(hb, LegacyHBChannel)
    finally:
        client.context.term()


def test_hb_channel_class_unrelated_typeerror_propagates_unchanged():
    """TypeError unrelated to curve_serverkey is not swallowed or re-wrapped."""

    class BrokenHBChannel(HBChannel):
        def __init__(self, context, session, address, **kwargs):  # type: ignore[override]
            raise TypeError("totally unrelated constructor error")

    pub, _sec = zmq.curve_keypair()

    client = KernelClient()
    client.hb_channel_class = BrokenHBChannel  # type: ignore[assignment]
    client.load_connection_info(
        {
            "ip": "127.0.0.1",
            "transport": "tcp",
            "hb_port": 5555,
            "key": "abc123",
            "signature_scheme": "hmac-sha256",
            "curve_publickey": pub.decode("ascii"),
            "curve_secretkey": pub.decode("ascii"),
        }
    )

    try:
        with pytest.raises(TypeError, match="totally unrelated constructor error"):
            _ = client.hb_channel
    finally:
        client.context.term()


def test_connect_shell_to_curve_server_without_curve_keys_is_rejected():
    """Public API path: without curve keys, shell traffic to a Curve server is dropped."""
    pub, sec = zmq.curve_keypair()

    ctx = zmq.Context()
    server = ctx.socket(zmq.ROUTER)
    server.curve_secretkey = sec
    server.curve_publickey = pub
    server.curve_server = True
    port = server.bind_to_random_port("tcp://127.0.0.1")

    try:
        info = {
            "ip": "127.0.0.1",
            "transport": "tcp",
            "shell_port": port,
            "key": "abc123",
            "signature_scheme": "hmac-sha256",
        }
        mixin = ConnectionFileMixin()
        mixin.context = ctx
        mixin.load_connection_info(info)

        client_sock = mixin.connect_shell()
        try:
            client_sock.send(b"probe", flags=zmq.NOBLOCK)
            poller = zmq.Poller()
            poller.register(server, zmq.POLLIN)
            events = dict(poller.poll(timeout=300))
            assert server not in events, (
                "Unauthenticated message reached Curve server - expected drop without curve keys"
            )
        finally:
            client_sock.close(linger=0)
    finally:
        server.close(linger=0)
        ctx.term()


def test_connect_shell_to_curve_server_with_wrong_curve_keys_is_rejected():
    """Public API path: mismatched curve keys - traffic to a Curve server is dropped."""
    pub, sec = zmq.curve_keypair()
    wrong_pub, wrong_sec = zmq.curve_keypair()

    ctx = zmq.Context()
    server = ctx.socket(zmq.ROUTER)
    server.curve_secretkey = sec
    server.curve_publickey = pub
    server.curve_server = True
    port = server.bind_to_random_port("tcp://127.0.0.1")

    try:
        info = {
            "ip": "127.0.0.1",
            "transport": "tcp",
            "shell_port": port,
            "key": "abc123",
            "signature_scheme": "hmac-sha256",
            "curve_publickey": wrong_pub.decode("ascii"),
            "curve_secretkey": wrong_sec.decode("ascii"),
        }
        mixin = ConnectionFileMixin()
        mixin.context = ctx
        mixin.load_connection_info(info)

        client_sock = mixin.connect_shell()
        try:
            client_sock.send(b"probe", flags=zmq.NOBLOCK)
            poller = zmq.Poller()
            poller.register(server, zmq.POLLIN)
            events = dict(poller.poll(timeout=300))
            assert server not in events, (
                "Message with wrong curve keys reached Curve server - expected drop"
            )
        finally:
            client_sock.close(linger=0)
    finally:
        server.close(linger=0)
        ctx.term()
