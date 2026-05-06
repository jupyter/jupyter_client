"""Tests for the ZMQ transport security."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import pytest
import zmq

from jupyter_client.channels import HBChannel
from jupyter_client.client import KernelClient
from jupyter_client.connect import ConnectionFileMixin
from jupyter_client.session import Session


@pytest.mark.parametrize(
    ("enable_curve", "expect_plaintext_visible"),
    [
        (False, True),
        (True, False),
    ],
)
def test_iopub_plaintext_visibility_depends_on_curve(enable_curve, expect_plaintext_visible):
    """An unauthenticated subscriber sees plaintext only when Curve is disabled."""

    ctx = zmq.Context()
    session = Session(key=b"secret-hmac-key")
    server = ctx.socket(zmq.XPUB)
    eavesdropper = ctx.socket(zmq.SUB)

    if enable_curve:
        pub, sec = zmq.curve_keypair()
        server.curve_secretkey = sec
        server.curve_publickey = pub
        server.curve_server = True

    try:
        port = server.bind_to_random_port("tcp://127.0.0.1")

        # Eavesdropper connects with no authentication or curve keys at all.
        eavesdropper.setsockopt(zmq.SUBSCRIBE, b"")
        eavesdropper.connect(f"tcp://127.0.0.1:{port}")

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
        recv_poller.register(eavesdropper, zmq.POLLIN)
        events = dict(recv_poller.poll(timeout=1000))

        did_receive = eavesdropper in events
        assert did_receive is expect_plaintext_visible, (
            "Unexpected unauthenticated visibility result for IOPub payload"
        )
        if expect_plaintext_visible:
            # Demonstrates that the message content is visible in plaintext frames when Curve is disabled.
            raw_frames = eavesdropper.recv_multipart()
            raw_bytes = b"".join(raw_frames)
            assert b"top_secret_output_12345" in raw_bytes, (
                f"Expected plaintext content in raw frames.\nRaw bytes: {raw_bytes!r}"
            )
            assert b"stream" in raw_bytes, "msg_type 'stream' should be visible in plaintext frames"

    finally:
        server.close(linger=0)
        eavesdropper.close(linger=0)
        ctx.term()


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

    with pytest.raises(RuntimeError, match="curve_serverkey"):
        _ = client.hb_channel


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

    hb = client.hb_channel
    assert isinstance(hb, LegacyHBChannel)


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
