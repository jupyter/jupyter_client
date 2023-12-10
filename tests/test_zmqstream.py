"""Tests for the ZMQStream"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from asyncio import Future

import zmq

from jupyter_client.ioloop.manager import ZMQStream


def create_bound_pair(
    context: zmq.Context, interface: str = "tcp://127.0.0.1"
) -> tuple[zmq.sugar.Socket, zmq.sugar.Socket]:
    """Create a bound socket pair using a random port."""

    s1 = context.socket(zmq.PAIR)
    s1.linger = 0
    port = s1.bind_to_random_port(interface)
    s2 = context.socket(zmq.PAIR)
    s2.linger = 0
    s2.connect(f"{interface}:{port}")
    return s1, s2


async def test_zqmstream():
    context = zmq.Context()
    sock1, sock2 = create_bound_pair(context)
    stream1 = ZMQStream(sock1)
    stream2 = ZMQStream(sock2)
    future = Future()

    def on_recv(msg):
        future.set_result(msg)

    stream1.on_recv(on_recv)
    stream2.send(b"ping")
    msg = await future
    assert msg == b"ping"
    future = Future()

    def on_send():
        future.set_result(None)

    stream1.on_send(on_send)
    stream1.send(b"pong")
    await future
    msg = stream2.recv()
    assert msg == b"pong"
    stream1.close()
    stream2.close()
    context.term()
