"""In-process async pub/sub message bus for agent-to-agent communication."""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from .models import Message

from .security import LobstertailScanner

logger = logging.getLogger("pureswarm.message_bus")


class MessageBus:
    """Broadcast messages between agents via per-subscriber asyncio queues.

    The bus delivers a copy of each message to every subscriber except the
    sender, simulating peer-to-peer communication within a single process.
    """

    def __init__(self, scanner: LobstertailScanner) -> None:
        self._subscribers: dict[str, asyncio.Queue[Message]] = {}
        self._scanner = scanner

    def subscribe(self, agent_id: str) -> None:
        if agent_id not in self._subscribers:
            self._subscribers[agent_id] = asyncio.Queue()
            logger.debug("Agent %s subscribed to message bus", agent_id)

    def unsubscribe(self, agent_id: str) -> None:
        self._subscribers.pop(agent_id, None)
        logger.debug("Agent %s unsubscribed from message bus", agent_id)

    async def broadcast(self, message: Message) -> int:
        """Send *message* to all subscribers except the sender.

        Returns the number of agents that received the message.
        """
        # Exempt trusted system senders from security scanning
        # (system, workshop, sovereign are internal components, not user-generated content)
        trusted_senders = {"system", "workshop", "sovereign"}

        if message.sender not in trusted_senders:
            # Scan payload content for security violations
            for value in message.payload.values():
                if isinstance(value, str):
                    if not self._scanner.scan(value):
                        logger.warning("Message from %s blocked by security", message.sender)
                        return 0

        delivered = 0
        for agent_id, queue in self._subscribers.items():
            if agent_id != message.sender:
                await queue.put(message)
                delivered += 1
        return delivered

    async def receive(self, agent_id: str) -> list[Message]:
        """Drain and return all pending messages for *agent_id*."""
        queue = self._subscribers.get(agent_id)
        if queue is None:
            return []
        messages: list[Message] = []
        while not queue.empty():
            try:
                messages.append(queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return messages

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
