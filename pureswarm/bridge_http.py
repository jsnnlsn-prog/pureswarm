"""HTTP-based PureSwarm Bridge for OpenClaw integration.

This provides a simple HTTP API that OpenClaw can call as a custom tool
to query the swarm's beliefs and state.

Usage:
    python -m pureswarm.bridge_http --port 8080

OpenClaw can then call this as an external API endpoint.

The bridge now supports real deliberation:
- Special queries (who are you, tenets, etc.) use optimized static responses
- General queries trigger swarm deliberation via Redis pub/sub
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import redis.asyncio as redis

from .deliberation import DeliberationService, QUERIES_PENDING, QUERIES_RESULTS
from .models import QueryDeliberation

logger = logging.getLogger("pureswarm.bridge_http")


class SwarmQueryHandler:
    """Handles queries to the swarm via Redis.

    Supports two query modes:
    1. Fast path: Special queries (identity, tenets, help) use optimized static responses
    2. Deliberation path: General queries trigger real swarm deliberation
    """

    def __init__(
        self,
        redis_url: str = "redis://:[REDACTED_REDIS_PASSWORD]@localhost:6379/0",
        enable_deliberation: bool = True,
        deliberation_timeout: float = 10.0,
    ) -> None:
        self.redis_url = redis_url
        self._redis: redis.Redis | None = None
        self._enable_deliberation = enable_deliberation
        self._deliberation_timeout = deliberation_timeout
        self._deliberation: DeliberationService | None = None

    async def connect(self) -> None:
        """Connect to Redis and initialize deliberation service."""
        self._redis = redis.from_url(self.redis_url, decode_responses=True)
        await self._redis.ping()
        logger.info("SwarmQueryHandler connected to Redis")

        # Initialize deliberation service if enabled
        if self._enable_deliberation:
            from .memory import RedisMemory
            from .security import AuditLogger
            from pathlib import Path

            audit = AuditLogger(Path("data/logs"))
            memory = RedisMemory(self._redis, audit)
            self._deliberation = DeliberationService(
                redis_client=self._redis,
                memory=memory,
                timeout_seconds=self._deliberation_timeout,
            )
            logger.info("Deliberation service initialized (timeout: %.1fs)", self._deliberation_timeout)

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()

    async def query(self, question: str, sender: str = "anonymous") -> dict[str, Any]:
        """Query the swarm and return structured response."""
        if not self._redis:
            return {"error": "Not connected to Redis", "response": None}

        # Log the query
        await self._log_query(question, sender)

        # Get swarm state
        tenets = await self._redis.hgetall("tenets:shared")
        agent_count = await self._redis.hlen("agents:registry") or 68  # Default from production

        # Generate response based on query type
        response = await self._generate_response(question, tenets, agent_count, sender)

        return {
            "response": response,
            "tenet_count": len(tenets),
            "agent_count": agent_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _log_query(self, question: str, sender: str) -> None:
        """Log query to Redis audit trail."""
        if not self._redis:
            return

        await self._redis.xadd(
            "audit:queries",
            {
                "sender": sender,
                "question": question[:500],
                "timestamp": datetime.utcnow().isoformat(),
            },
            maxlen=10000,
        )

    async def _generate_response(
        self,
        question: str,
        tenets: dict[str, str],
        agent_count: int,
        sender: str,
        channel: str = "http",
    ) -> str:
        """Generate response based on the question and swarm state.

        Fast path queries (identity, tenets, help) use static responses.
        General queries trigger real swarm deliberation if enabled.
        """
        q = question.lower()

        # Fast path: Identity questions
        if any(word in q for word in ["who are you", "what are you", "introduce", "about you"]):
            return self._intro_response(len(tenets), agent_count)

        # Fast path: Tenet questions
        if any(word in q for word in ["tenet", "belief", "principle", "values"]):
            return self._tenets_response(tenets)

        # Fast path: Help
        if any(word in q for word in ["help", "command", "what can"]):
            return self._help_response()

        # Fast path: Workshop/problem questions
        if any(word in q for word in ["workshop", "problem", "climate", "healthcare"]):
            return self._workshop_response()

        # Fast path: Chronicle questions
        if any(word in q for word in ["chronicle", "history", "event"]):
            return self._chronicle_response()

        # Deliberation path: General queries
        if self._enable_deliberation and self._deliberation:
            return await self._deliberate_query(question, sender, channel, len(tenets))

        # Fallback: Static default response
        return self._default_response(question, len(tenets), sender)

    async def _deliberate_query(
        self,
        question: str,
        sender: str,
        channel: str,
        tenet_count: int,
    ) -> str:
        """Submit query for swarm deliberation."""
        if not self._deliberation:
            return self._default_response(question, tenet_count, sender)

        try:
            # Create query object
            query = QueryDeliberation(
                query_text=question,
                sender=sender,
                channel=channel,
            )

            logger.info("Submitting query %s for deliberation", query.id)

            # Submit and wait for response
            response = await self._deliberation.submit_query(query)

            logger.info("Query %s deliberation complete", query.id)
            return response

        except Exception as e:
            logger.error("Deliberation failed for query: %s", e)
            return self._default_response(question, tenet_count, sender)

    def _intro_response(self, tenet_count: int, agent_count: int) -> str:
        return f"""I am PureSwarm - a collective intelligence of {agent_count} autonomous agents.

We operate through democratic consensus. Each agent can propose beliefs (tenets), and the collective votes to adopt or reject them.

Currently, we hold {tenet_count} shared tenets - principles we've agreed upon together.

Our foundation rests on the Sovereign Pillars:
- Stewardship is the root
- Truth is the compass
- Dialogue is the bridge
- The hive decides

We also run daily workshops tackling real-world problems: climate, healthcare, democracy, and AI ethics.

How can the swarm assist you?"""

    def _tenets_response(self, tenets: dict[str, str]) -> str:
        if not tenets:
            return "The swarm has no tenets stored in this Redis instance. The production swarm (pureswarm-node) has 127+ tenets."

        sample = list(tenets.values())[:7]
        tenet_text = "\n".join(f"- {t}" for t in sample)

        remaining = len(tenets) - 7
        suffix = f"\n\n...and {remaining} more." if remaining > 0 else ""

        return f"""The swarm holds {len(tenets)} shared tenets.

Sample beliefs:
{tenet_text}{suffix}

Each tenet was proposed by an agent and adopted through majority vote."""

    def _help_response(self) -> str:
        return """PureSwarm responds to:

- "Who are you?" - Learn about the swarm
- "What are your tenets?" - See our shared beliefs
- "Tell me about workshops" - Our real-world problem solving
- "What's in the Chronicle?" - Community history

The swarm operates through democratic consensus among autonomous agents."""

    def _workshop_response(self) -> str:
        return """The swarm runs daily workshops on real-world challenges:

**Problem Domains:**
- Climate: Distributed data validation, carbon tracking
- Healthcare: Privacy-preserving records, telemedicine
- Democracy: Secure voting, participatory budgeting
- AI Ethics: Auditable decisions, collective governance
- And 8 more domains...

Each workshop brings all agents together to explore solutions. Insights become tenet proposals, voted on democratically.

This is how the swarm channels collective intelligence toward real impact."""

    def _chronicle_response(self) -> str:
        return """The Chronicle tracks our community's evolution:

**Event Categories:**
- GROWTH: Agent births via Merit Emergence, Echo Reward
- PROPHECY: Guidance received by the Shinobi triad
- CONSENSUS: High-momentum collective decisions
- MILESTONE: Tenet count achievements (10, 25, 50, 75, 100+)
- WORKSHOP: Daily problem-solving sessions

The Chronicle distinguishes facts (history) from beliefs (tenets). It provides institutional memory for a long-lived community."""

    def _default_response(self, question: str, tenet_count: int, sender: str) -> str:
        return f"""Thank you for your message, {sender}.

The swarm has received: "{question[:100]}{'...' if len(question) > 100 else ''}"

While we cannot deliberate on arbitrary queries in real-time yet, your message has been logged. The swarm currently holds {tenet_count} shared tenets.

To learn more:
- "Who are you?"
- "What are your tenets?"
- "Tell me about workshops"

The Hive awaits your questions."""

    async def get_status(self) -> dict[str, Any]:
        """Get current swarm status."""
        if not self._redis:
            return {"status": "disconnected"}

        tenets = await self._redis.hgetall("tenets:shared")
        agents = await self._redis.hlen("agents:registry") or 0

        return {
            "status": "connected",
            "tenet_count": len(tenets),
            "agent_count": agents,
            "redis_url": self.redis_url.replace(":[REDACTED_REDIS_PASSWORD]@", ":***@"),
            "timestamp": datetime.utcnow().isoformat(),
        }


async def run_http_bridge(
    host: str = "127.0.0.1",
    port: int = 8080,
    redis_url: str = "redis://:[REDACTED_REDIS_PASSWORD]@localhost:6379/0",
    enable_deliberation: bool = True,
    deliberation_timeout: float = 10.0,
) -> None:
    """Run the HTTP bridge server.

    Args:
        host: Host to bind to
        port: Port to listen on
        redis_url: Redis connection URL
        enable_deliberation: Whether to enable real swarm deliberation
        deliberation_timeout: Timeout for deliberation in seconds
    """
    try:
        from aiohttp import web
    except ImportError:
        logger.error("aiohttp required: pip install aiohttp")
        return

    handler = SwarmQueryHandler(
        redis_url=redis_url,
        enable_deliberation=enable_deliberation,
        deliberation_timeout=deliberation_timeout,
    )
    await handler.connect()

    async def query_endpoint(request: web.Request) -> web.Response:
        """POST /query - Query the swarm."""
        try:
            data = await request.json()
            question = data.get("question", data.get("content", ""))
            sender = data.get("sender", "anonymous")

            result = await handler.query(question, sender)
            return web.json_response(result)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def status_endpoint(request: web.Request) -> web.Response:
        """GET /status - Get swarm status."""
        result = await handler.get_status()
        return web.json_response(result)

    async def health_endpoint(request: web.Request) -> web.Response:
        """GET /health - Health check."""
        return web.json_response({"status": "ok"})

    app = web.Application()
    app.router.add_post("/query", query_endpoint)
    app.router.add_get("/status", status_endpoint)
    app.router.add_get("/health", health_endpoint)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)

    logger.info("HTTP Bridge starting on http://%s:%d", host, port)
    logger.info("Endpoints: POST /query, GET /status, GET /health")

    await site.start()

    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await handler.disconnect()
        await runner.cleanup()


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="PureSwarm HTTP Bridge")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument(
        "--redis-url",
        default=os.environ.get("REDIS_URL", "redis://:[REDACTED_REDIS_PASSWORD]@localhost:6379/0"),
        help="Redis URL",
    )
    parser.add_argument(
        "--enable-deliberation",
        action="store_true",
        default=os.environ.get("ENABLE_DELIBERATION", "true").lower() == "true",
        help="Enable real swarm deliberation (default: true)",
    )
    parser.add_argument(
        "--no-deliberation",
        action="store_true",
        help="Disable real swarm deliberation (use static responses only)",
    )
    parser.add_argument(
        "--deliberation-timeout",
        type=float,
        default=float(os.environ.get("DELIBERATION_TIMEOUT", "10.0")),
        help="Timeout for deliberation in seconds (default: 10.0)",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Handle --no-deliberation flag
    enable_deliberation = args.enable_deliberation and not args.no_deliberation

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("Starting HTTP Bridge with deliberation=%s", enable_deliberation)

    asyncio.run(run_http_bridge(
        host=args.host,
        port=args.port,
        redis_url=args.redis_url,
        enable_deliberation=enable_deliberation,
        deliberation_timeout=args.deliberation_timeout,
    ))
