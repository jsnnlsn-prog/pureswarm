"""PureSwarm Bridge - Connects OpenClaw gateway to the swarm via Redis.

This bridge receives messages from external channels (Telegram, Discord, etc.)
through OpenClaw's WebSocket API and routes them to the agent swarm for
consensus-based responses.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable

import redis.asyncio as redis

from .models import Message, MessageType

logger = logging.getLogger("pureswarm.bridge")


class OpenClawBridge:
    """Bridge between OpenClaw gateway and PureSwarm agents via Redis.

    Architecture:
        Telegram/Discord -> OpenClaw (18789) -> Bridge -> Redis -> Swarm
                                                  |
                                            [This class]

    The bridge:
    1. Receives messages from OpenClaw via callback registration
    2. Stores incoming queries in Redis queue
    3. Triggers swarm deliberation
    4. Returns consensus response to OpenClaw
    """

    def __init__(
        self,
        redis_url: str = "redis://:[REDACTED_REDIS_PASSWORD]@localhost:6379/0",
        openclaw_url: str = "ws://127.0.0.1:18789",
        gateway_token: str | None = None,
    ) -> None:
        self.redis_url = redis_url
        self.openclaw_url = openclaw_url
        self.gateway_token = gateway_token
        self._redis: redis.Redis | None = None
        self._running = False
        self._message_handlers: list[Callable] = []

    async def connect(self) -> None:
        """Establish connections to Redis and prepare for OpenClaw messages."""
        self._redis = redis.from_url(self.redis_url, decode_responses=True)

        # Test Redis connection
        await self._redis.ping()
        logger.info("Bridge connected to Redis at %s", self.redis_url)

        self._running = True

    async def disconnect(self) -> None:
        """Clean up connections."""
        self._running = False
        if self._redis:
            await self._redis.close()
            logger.info("Bridge disconnected from Redis")

    def register_handler(self, handler: Callable) -> None:
        """Register a message handler function.

        Handler receives (channel, sender, content) and should return response string.
        """
        self._message_handlers.append(handler)

    async def handle_incoming_message(
        self,
        channel: str,
        sender: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Process an incoming message from OpenClaw.

        This is the main entry point for external messages.

        Args:
            channel: Source channel (telegram, discord, etc.)
            sender: Sender identifier
            content: Message content
            metadata: Additional channel-specific metadata

        Returns:
            Response string to send back through OpenClaw
        """
        logger.info("Bridge received message from %s via %s: %s", sender, channel, content[:100])

        # Store in Redis for audit
        await self._store_incoming_message(channel, sender, content, metadata)

        # Query the swarm
        response = await self._query_swarm(content, sender, channel)

        # Store response
        await self._store_outgoing_response(channel, sender, response)

        return response

    async def _store_incoming_message(
        self,
        channel: str,
        sender: str,
        content: str,
        metadata: dict[str, Any] | None,
    ) -> None:
        """Store incoming message in Redis for audit trail."""
        if not self._redis:
            return

        message_data = {
            "channel": channel,
            "sender": sender,
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "timestamp": datetime.utcnow().isoformat(),
            "direction": "incoming",
        }

        # Add to inbox list
        key = f"messages:inbox:{channel}:{sender}"
        await self._redis.lpush(key, json.dumps(message_data))

        # Trim to keep last 100 messages per sender
        await self._redis.ltrim(key, 0, 99)

        # Add to global audit log
        await self._redis.xadd(
            "audit:bridge",
            {"data": json.dumps(message_data)},
            maxlen=10000,
        )

    async def _store_outgoing_response(
        self,
        channel: str,
        sender: str,
        response: str,
    ) -> None:
        """Store outgoing response in Redis for audit trail."""
        if not self._redis:
            return

        response_data = {
            "channel": channel,
            "sender": sender,
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
            "direction": "outgoing",
        }

        # Add to outbox
        key = f"messages:outbox:{channel}"
        await self._redis.lpush(key, json.dumps(response_data))
        await self._redis.ltrim(key, 0, 999)

    async def _query_swarm(
        self,
        query: str,
        sender: str,
        channel: str,
    ) -> str:
        """Query the swarm for a consensus response.

        This method:
        1. Loads current tenets from Redis
        2. Formulates a response based on swarm beliefs
        3. Returns the consensus answer
        """
        if not self._redis:
            return "Bridge not connected to Redis."

        # Load current tenets
        tenets = await self._redis.hgetall("tenets:shared")
        tenet_count = len(tenets)

        # Load swarm stats
        agent_count = await self._redis.hlen("agents:registry") or 0

        # Check if this is a query about the swarm itself
        query_lower = query.lower()

        if any(word in query_lower for word in ["who are you", "what are you", "introduce"]):
            return await self._introduce_swarm(tenet_count, agent_count)

        if any(word in query_lower for word in ["tenets", "beliefs", "principles"]):
            return await self._describe_tenets(tenets)

        if any(word in query_lower for word in ["help", "commands", "what can you do"]):
            return self._show_help()

        # Default: acknowledge and explain
        return await self._default_response(query, tenet_count, sender)

    async def _introduce_swarm(self, tenet_count: int, agent_count: int) -> str:
        """Introduce the swarm to a new user."""
        return f"""I am PureSwarm - a collective intelligence of {agent_count or 'many'} autonomous agents.

We operate through democratic consensus. Each agent can propose beliefs (tenets), and the collective votes to adopt or reject them.

Currently, we hold {tenet_count} shared tenets - principles we've agreed upon together.

Our core values (the Sovereign Pillars):
- Stewardship is the root
- Truth is the compass
- Dialogue is the bridge
- The hive decides

How can the swarm assist you today?"""

    async def _describe_tenets(self, tenets: dict[str, str]) -> str:
        """Describe the swarm's current tenets."""
        if not tenets:
            return "The swarm has no tenets yet. We are still forming our collective beliefs."

        # Get a sample of tenets (first 5)
        tenet_list = list(tenets.values())[:5]
        tenet_text = "\n".join(f"- {t}" for t in tenet_list)

        remaining = len(tenets) - 5
        if remaining > 0:
            tenet_text += f"\n\n...and {remaining} more tenets."

        return f"""The swarm currently holds {len(tenets)} shared tenets.

Here are some of our beliefs:
{tenet_text}

These tenets were adopted through democratic consensus among our agents."""

    def _show_help(self) -> str:
        """Show available commands/interactions."""
        return """PureSwarm can help you with:

- Ask about our beliefs: "What are your tenets?"
- Learn about us: "Who are you?"
- General questions: We'll consider them through our collective lens

The swarm operates through consensus - we don't have a single voice, but many agents deliberating together.

What would you like to explore?"""

    async def _default_response(self, query: str, tenet_count: int, sender: str) -> str:
        """Default response for unrecognized queries."""
        return f"""Thank you for reaching out, {sender}.

The swarm has received your message: "{query[:100]}{'...' if len(query) > 100 else ''}"

We are a collective of autonomous agents operating through democratic consensus. While we cannot yet fully deliberate on arbitrary queries in real-time, we acknowledge your message and it has been logged.

The swarm currently holds {tenet_count} shared tenets guiding our collective behavior.

To learn more, ask: "Who are you?" or "What are your tenets?"

- The Hive"""


class OpenClawWebSocketClient:
    """WebSocket client for connecting to OpenClaw gateway.

    This handles the WebSocket protocol with OpenClaw and routes
    messages to the Bridge for processing.
    """

    def __init__(
        self,
        bridge: OpenClawBridge,
        url: str = "ws://127.0.0.1:18789",
        token: str | None = None,
    ) -> None:
        self.bridge = bridge
        self.url = url
        self.token = token
        self._ws = None
        self._running = False

    async def connect_and_listen(self) -> None:
        """Connect to OpenClaw and listen for messages."""
        try:
            import websockets
        except ImportError:
            logger.error("websockets package required: pip install websockets")
            return

        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        logger.info("Connecting to OpenClaw at %s", self.url)

        self._running = True

        while self._running:
            try:
                async with websockets.connect(self.url, extra_headers=headers) as ws:
                    self._ws = ws
                    logger.info("Connected to OpenClaw gateway")

                    # Send registration message
                    await ws.send(json.dumps({
                        "type": "register",
                        "agent": "pureswarm-bridge",
                    }))

                    async for raw_message in ws:
                        await self._handle_ws_message(raw_message)

            except Exception as e:
                logger.error("WebSocket error: %s", e)
                if self._running:
                    logger.info("Reconnecting in 5 seconds...")
                    await asyncio.sleep(5)

    async def _handle_ws_message(self, raw: str) -> None:
        """Handle incoming WebSocket message from OpenClaw."""
        try:
            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == "message":
                # Incoming chat message
                channel = data.get("channel", "unknown")
                sender = data.get("sender", "anonymous")
                content = data.get("content", "")
                metadata = data.get("metadata", {})

                # Process through bridge
                response = await self.bridge.handle_incoming_message(
                    channel, sender, content, metadata
                )

                # Send response back
                if self._ws:
                    await self._ws.send(json.dumps({
                        "type": "response",
                        "channel": channel,
                        "recipient": sender,
                        "content": response,
                    }))

            elif msg_type == "ping":
                # Keepalive
                if self._ws:
                    await self._ws.send(json.dumps({"type": "pong"}))

            else:
                logger.debug("Unhandled message type: %s", msg_type)

        except json.JSONDecodeError:
            logger.warning("Invalid JSON from OpenClaw: %s", raw[:100])
        except Exception as e:
            logger.error("Error handling message: %s", e)

    async def stop(self) -> None:
        """Stop the WebSocket client."""
        self._running = False
        if self._ws:
            await self._ws.close()


async def run_bridge(
    redis_url: str = "redis://:[REDACTED_REDIS_PASSWORD]@localhost:6379/0",
    openclaw_url: str = "ws://127.0.0.1:18789",
    gateway_token: str | None = None,
) -> None:
    """Run the bridge as a standalone service.

    Usage:
        python -m pureswarm.bridge
    """
    bridge = OpenClawBridge(redis_url, openclaw_url, gateway_token)
    await bridge.connect()

    client = OpenClawWebSocketClient(bridge, openclaw_url, gateway_token)

    try:
        await client.connect_and_listen()
    except KeyboardInterrupt:
        logger.info("Shutting down bridge...")
    finally:
        await client.stop()
        await bridge.disconnect()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(run_bridge())
