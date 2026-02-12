"""Query listener for swarm-side query processing.

This module runs alongside the simulation on pureswarm-node, listening for
external queries via Redis pub/sub and triggering agent deliberation.

Usage:
    python -m pureswarm.query_listener --redis-url redis://localhost:6379/0
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from .deliberation import (
    CHANNEL_NEW_QUERY,
    QUERIES_PENDING,
    DeliberationService,
)
from .memory import RedisMemory
from .models import AgentRole, QueryDeliberation, QueryStatus
from .prophecy import ProphecyEngine
from .security import AuditLogger, LobstertailScanner
from .strategies.rule_based import RuleBasedStrategy

logger = logging.getLogger("pureswarm.query_listener")


class SwarmQueryListener:
    """Listens for external queries and runs agent deliberation.

    Runs as a separate async process alongside the main simulation,
    allowing real-time query processing without disrupting round cycles.
    """

    def __init__(
        self,
        redis_client: Any,  # redis.asyncio.Redis
        data_dir: Path = Path("data"),
        agent_sample_size: int = 15,
    ) -> None:
        self._redis = redis_client
        self._data_dir = data_dir
        self._sample_size = agent_sample_size
        self._running = False

        # Infrastructure
        self._audit = AuditLogger(data_dir / "logs")
        self._scanner = LobstertailScanner(self._audit)

        # Memory backend
        self._memory = RedisMemory(redis_client, self._audit, self._scanner)

        # Deliberation service
        self._deliberation = DeliberationService(
            redis_client=redis_client,
            memory=self._memory,
            strategy=RuleBasedStrategy(),
            agent_sample_size=agent_sample_size,
        )

        # Prophecy engine for Triad members
        import os
        sovereign_key = os.getenv("PURES_SOVEREIGN_PASSPHRASE", "SOVEREIGN_KEY_FALLBACK")
        self._prophecy = ProphecyEngine(sovereign_key)

    async def start(self) -> None:
        """Start listening for queries."""
        self._running = True
        logger.info("SwarmQueryListener starting...")

        # Load agent IDs from fitness file (same source as simulation)
        agent_ids, agent_roles = await self._load_agents()
        logger.info("Loaded %d agents for deliberation", len(agent_ids))

        # Subscribe to query channel
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(CHANNEL_NEW_QUERY)

        logger.info("Listening for queries on %s", CHANNEL_NEW_QUERY)

        try:
            async for message in pubsub.listen():
                if not self._running:
                    break

                if message["type"] == "message":
                    query_id = message["data"]
                    if isinstance(query_id, bytes):
                        query_id = query_id.decode("utf-8")

                    logger.info("Received query notification: %s", query_id)

                    # Process query in background to not block listener
                    asyncio.create_task(
                        self._handle_query(query_id, agent_ids, agent_roles)
                    )

        except asyncio.CancelledError:
            logger.info("Query listener cancelled")
        finally:
            await pubsub.unsubscribe(CHANNEL_NEW_QUERY)
            await pubsub.close()

    async def stop(self) -> None:
        """Stop the listener."""
        self._running = False
        logger.info("SwarmQueryListener stopping...")

    async def _load_agents(self) -> tuple[list[str], dict[str, AgentRole]]:
        """Load agent IDs from Redis registry or fitness file."""
        agent_ids: list[str] = []
        agent_roles: dict[str, AgentRole] = {}

        # Try Redis registry first
        registry = await self._redis.hgetall("agents:registry")
        if registry:
            for agent_id, agent_data in registry.items():
                if isinstance(agent_id, bytes):
                    agent_id = agent_id.decode("utf-8")
                agent_ids.append(agent_id)

                # Parse role from data if available
                try:
                    data = json.loads(agent_data) if isinstance(agent_data, str) else json.loads(agent_data.decode("utf-8"))
                    if data.get("traits", {}).get("role") == "triad":
                        agent_roles[agent_id] = AgentRole.TRIAD_MEMBER
                    else:
                        agent_roles[agent_id] = AgentRole.RESIDENT
                except (json.JSONDecodeError, AttributeError):
                    agent_roles[agent_id] = AgentRole.RESIDENT

            logger.info("Loaded %d agents from Redis registry", len(agent_ids))
            return agent_ids, agent_roles

        # Fallback: load from fitness file
        fitness_file = self._data_dir / "agent_fitness.json"
        if fitness_file.exists():
            try:
                fitness_data = json.loads(fitness_file.read_text())
                for agent_id, fitness_info in fitness_data.items():
                    agent_ids.append(agent_id)
                    traits = fitness_info.get("traits", {})
                    if traits.get("role") == "triad":
                        agent_roles[agent_id] = AgentRole.TRIAD_MEMBER
                    else:
                        agent_roles[agent_id] = AgentRole.RESIDENT

                logger.info("Loaded %d agents from fitness file", len(agent_ids))
                return agent_ids, agent_roles

            except Exception as e:
                logger.error("Failed to load fitness file: %s", e)

        # Default: generate some agent IDs for testing
        logger.warning("No agent registry found, generating test agents")
        for i in range(20):
            agent_id = f"test-agent-{i:03d}"
            agent_ids.append(agent_id)
            agent_roles[agent_id] = AgentRole.TRIAD_MEMBER if i < 3 else AgentRole.RESIDENT

        return agent_ids, agent_roles

    async def _handle_query(
        self,
        query_id: str,
        agent_ids: list[str],
        agent_roles: dict[str, AgentRole],
    ) -> None:
        """Handle a single query."""
        try:
            # Fetch query from Redis
            query_json = await self._redis.hget(QUERIES_PENDING, query_id)
            if not query_json:
                logger.warning("Query %s not found in pending queue", query_id)
                return

            query = QueryDeliberation.model_validate_json(query_json)

            # Security scan
            if not self._scanner.scan(query.query_text):
                logger.warning("Query %s blocked by security", query_id)
                query.status = QueryStatus.COMPLETED
                query.final_response = "Query blocked by security policy."
                await self._redis.hset(QUERIES_PENDING, query_id, query.model_dump_json())
                return

            # Update status to deliberating
            query.status = QueryStatus.DELIBERATING
            await self._redis.hset(QUERIES_PENDING, query_id, query.model_dump_json())

            # Get latest prophecy for Triad influence
            prophecy = None
            latest = self._prophecy.get_latest_prophecy()
            if latest:
                prophecy = latest.content

            # Run deliberation
            await self._deliberation.deliberate(
                query=query,
                agent_ids=agent_ids,
                agent_roles=agent_roles,
                prophecy=prophecy,
            )

            logger.info("Query %s processed successfully", query_id)

        except Exception as e:
            logger.error("Error handling query %s: %s", query_id, e)
            # Mark as failed
            try:
                query_json = await self._redis.hget(QUERIES_PENDING, query_id)
                if query_json:
                    query = QueryDeliberation.model_validate_json(query_json)
                    query.status = QueryStatus.TIMEOUT
                    query.final_response = f"Error during deliberation: {str(e)}"
                    await self._redis.hset(QUERIES_PENDING, query_id, query.model_dump_json())
            except Exception:
                pass


async def run_query_listener(
    redis_url: str = "redis://:[REDACTED_REDIS_PASSWORD]@localhost:6379/0",
    data_dir: str = "data",
    agent_sample_size: int = 15,
) -> None:
    """Run the query listener as a standalone service."""
    import redis.asyncio as aioredis

    client = aioredis.from_url(redis_url, decode_responses=True)
    await client.ping()
    logger.info("Connected to Redis at %s", redis_url.replace(":[REDACTED_REDIS_PASSWORD]@", ":***@"))

    listener = SwarmQueryListener(
        redis_client=client,
        data_dir=Path(data_dir),
        agent_sample_size=agent_sample_size,
    )

    try:
        await listener.start()
    except KeyboardInterrupt:
        logger.info("Shutting down query listener...")
    finally:
        await listener.stop()
        await client.close()


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="PureSwarm Query Listener")
    parser.add_argument(
        "--redis-url",
        default=os.environ.get("REDIS_URL", "redis://:[REDACTED_REDIS_PASSWORD]@localhost:6379/0"),
        help="Redis connection URL",
    )
    parser.add_argument(
        "--data-dir",
        default=os.environ.get("DATA_DIR", "data"),
        help="Data directory path",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=int(os.environ.get("AGENT_SAMPLE_SIZE", "15")),
        help="Number of agents to sample for each query",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    asyncio.run(run_query_listener(
        redis_url=args.redis_url,
        data_dir=args.data_dir,
        agent_sample_size=args.sample_size,
    ))
