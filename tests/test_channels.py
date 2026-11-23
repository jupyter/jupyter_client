"""Tests for ZMQ channel helpers."""

from queue import Empty
from unittest.mock import AsyncMock, Mock, call

from jupyter_client.channels import AsyncZMQSocketChannel, ZMQSocketChannel


def test_get_msgs_only_reads_ready_messages():
    channel = object.__new__(ZMQSocketChannel)
    channel.get_msg = Mock(side_effect=[{"id": 1}, {"id": 2}, Empty])

    assert channel.get_msgs() == [{"id": 1}, {"id": 2}]
    assert channel.get_msg.call_args_list == [call(timeout=0)] * 3


async def test_async_get_msgs_only_reads_ready_messages():
    channel = object.__new__(AsyncZMQSocketChannel)
    channel.get_msg = AsyncMock(side_effect=[{"id": 1}, {"id": 2}, Empty])

    assert await channel.get_msgs() == [{"id": 1}, {"id": 2}]
    assert channel.get_msg.call_args_list == [call(timeout=0)] * 3
