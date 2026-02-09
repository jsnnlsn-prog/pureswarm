"""Tests for the message bus."""

import asyncio
import pytest
from pureswarm.message_bus import MessageBus
from pureswarm.models import Message, MessageType


@pytest.fixture
def bus():
    return MessageBus()


@pytest.mark.asyncio
async def test_subscribe_and_broadcast(bus):
    bus.subscribe("a1")
    bus.subscribe("a2")
    bus.subscribe("a3")
    assert bus.subscriber_count == 3

    msg = Message(sender="a1", type=MessageType.OBSERVATION, payload={"data": "hello"})
    delivered = await bus.broadcast(msg)
    assert delivered == 2  # everyone except sender

    # a1 should have no messages, a2 and a3 should have one each
    assert await bus.receive("a1") == []
    msgs_a2 = await bus.receive("a2")
    assert len(msgs_a2) == 1
    assert msgs_a2[0].payload["data"] == "hello"


@pytest.mark.asyncio
async def test_unsubscribe(bus):
    bus.subscribe("a1")
    bus.subscribe("a2")
    bus.unsubscribe("a2")
    assert bus.subscriber_count == 1

    msg = Message(sender="a1", type=MessageType.OBSERVATION)
    delivered = await bus.broadcast(msg)
    assert delivered == 0  # only a1 left, who is the sender


@pytest.mark.asyncio
async def test_receive_empty(bus):
    bus.subscribe("a1")
    msgs = await bus.receive("a1")
    assert msgs == []


@pytest.mark.asyncio
async def test_receive_nonexistent(bus):
    msgs = await bus.receive("unknown")
    assert msgs == []
