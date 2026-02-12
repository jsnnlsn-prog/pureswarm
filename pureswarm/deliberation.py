"""Deliberation service for real-time query processing.

This module enables the swarm to deliberate on external queries in near-real-time,
producing collective responses based on agent perspectives and shared tenets.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import datetime, timezone
from typing import Any

from .memory import MemoryBackend
from .models import (
    AgentRole,
    QueryDeliberation,
    QueryResponse,
    QueryStatus,
    Tenet,
)
from .strategies.base import BaseStrategy
from .strategies.rule_based import RuleBasedStrategy

logger = logging.getLogger("pureswarm.deliberation")

# Redis keys for query coordination
QUERIES_PENDING = "queries:pending"
QUERIES_RESULTS = "queries:results"
CHANNEL_NEW_QUERY = "pureswarm:queries:new"
CHANNEL_QUERY_COMPLETE = "pureswarm:queries:complete"


class DeliberationService:
    """Handles real-time query deliberation without disrupting round cycle.

    The service can run in two modes:
    1. Bridge-side (on pureswarm-test): Publishes queries, waits for responses
    2. Swarm-side (on pureswarm-node): Listens for queries, runs agent deliberation
    """

    def __init__(
        self,
        redis_client: Any,  # redis.asyncio.Redis
        memory: MemoryBackend,
        strategy: BaseStrategy | None = None,
        agent_sample_size: int = 15,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._redis = redis_client
        self._memory = memory
        self._strategy = strategy or RuleBasedStrategy()
        self._sample_size = agent_sample_size
        self._timeout = timeout_seconds

    async def submit_query(self, query: QueryDeliberation) -> str:
        """Submit a query for deliberation and wait for response.

        This is called by the bridge when an external query arrives.
        Returns the collective response string.
        """
        # Store query in Redis
        query_json = query.model_dump_json()
        await self._redis.hset(QUERIES_PENDING, query.id, query_json)

        # Notify swarm of new query
        await self._redis.publish(CHANNEL_NEW_QUERY, query.id)

        logger.info("Query %s submitted for deliberation: %s", query.id, query.query_text[:50])

        # Wait for response with timeout
        try:
            response = await asyncio.wait_for(
                self._wait_for_response(query.id),
                timeout=self._timeout,
            )
            return response
        except asyncio.TimeoutError:
            logger.warning("Query %s timed out after %.1fs", query.id, self._timeout)
            # Return fallback response based on tenets
            return await self._fallback_response(query)

    async def _wait_for_response(self, query_id: str) -> str:
        """Poll for query completion."""
        while True:
            result = await self._redis.hget(QUERIES_RESULTS, query_id)
            if result:
                # Parse result and return final response
                result_data = json.loads(result)
                return result_data.get("final_response", "The swarm has no response.")
            await asyncio.sleep(0.1)

    async def _fallback_response(self, query: QueryDeliberation) -> str:
        """Generate fallback response using local tenets when swarm is unavailable."""
        tenets = await self._memory.read_tenets()
        tenet_count = len(tenets)

        if not tenets:
            return f"The swarm acknowledges your query but has no tenets to guide its response yet."

        # Find relevant tenets
        query_words = set(query.query_text.lower().split())
        relevant = []
        for tenet in tenets:
            tenet_words = set(tenet.text.lower().split())
            overlap = len(query_words & tenet_words) / max(len(query_words), 1)
            if overlap > 0.1:
                relevant.append((overlap, tenet))

        relevant.sort(reverse=True)
        top_tenets = [t for _, t in relevant[:3]]

        if top_tenets:
            tenet_texts = "; ".join(t.text[:60] for t in top_tenets)
            return (
                f"The swarm (holding {tenet_count} tenets) offers guidance from our beliefs: {tenet_texts}. "
                f"[Response generated from tenets - full deliberation unavailable]"
            )
        else:
            return (
                f"The swarm (holding {tenet_count} tenets) acknowledges your query. "
                f"We have no specific tenets addressing this topic yet."
            )

    async def deliberate(
        self,
        query: QueryDeliberation,
        agent_ids: list[str],
        agent_roles: dict[str, AgentRole] | None = None,
        prophecy: str | None = None,
    ) -> str:
        """Run deliberation with specified agents and return collective response.

        This is called by the query listener on the swarm side.
        """
        agent_roles = agent_roles or {}

        # Load current tenets
        tenets = await self._memory.read_tenets()

        # Sample agents if we have more than sample size
        if len(agent_ids) > self._sample_size:
            sampled = random.sample(agent_ids, self._sample_size)
        else:
            sampled = agent_ids

        logger.info(
            "Deliberating query %s with %d agents (sampled from %d)",
            query.id,
            len(sampled),
            len(agent_ids),
        )

        # Gather responses from agents
        responses: list[QueryResponse] = []
        for agent_id in sampled:
            role = agent_roles.get(agent_id, AgentRole.RESIDENT)
            response = self._strategy.evaluate_query(
                agent_id=agent_id,
                query_text=query.query_text,
                existing_tenets=tenets,
                seed_prompt="",  # Not used in query evaluation
                role=role,
                prophecy=prophecy,
            )
            responses.append(response)

        # Aggregate responses
        final_response = self._aggregate_responses(responses, query, tenets)

        # Store result in Redis
        result_data = {
            "query_id": query.id,
            "final_response": final_response,
            "response_count": len(responses),
            "agent_sample_size": len(sampled),
            "total_agents": len(agent_ids),
            "tenet_count": len(tenets),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._redis.hset(QUERIES_RESULTS, query.id, json.dumps(result_data))

        # Notify bridge of completion
        await self._redis.publish(CHANNEL_QUERY_COMPLETE, query.id)

        # Update query status
        query.status = QueryStatus.COMPLETED
        query.final_response = final_response
        query.completed_at = datetime.now(timezone.utc)
        await self._redis.hset(QUERIES_PENDING, query.id, query.model_dump_json())

        logger.info("Query %s deliberation complete with %d responses", query.id, len(responses))

        return final_response

    def _aggregate_responses(
        self,
        responses: list[QueryResponse],
        query: QueryDeliberation,
        tenets: list[Tenet],
    ) -> str:
        """Combine agent responses into a collective answer.

        Aggregation strategy:
        1. Weight responses by confidence
        2. Extract common themes/insights
        3. Include specialty contributions
        4. Ensure tenet coherence
        """
        if not responses:
            return "The swarm has no response at this time."

        # Calculate average confidence
        avg_confidence = sum(r.confidence for r in responses) / len(responses)

        # Collect unique insights (deduplicated by similarity)
        insights: list[str] = []
        seen_phrases: set[str] = set()
        for response in sorted(responses, key=lambda r: r.confidence, reverse=True):
            # Extract key phrases (simple approach: sentences)
            for sentence in response.response_text.split(". "):
                sentence = sentence.strip()
                if not sentence:
                    continue
                # Check if similar phrase already seen
                words = set(sentence.lower().split())
                is_duplicate = False
                for seen in seen_phrases:
                    seen_words = set(seen.lower().split())
                    overlap = len(words & seen_words) / max(len(words), 1)
                    if overlap > 0.6:
                        is_duplicate = True
                        break
                if not is_duplicate and len(sentence) > 10:
                    insights.append(sentence)
                    seen_phrases.add(sentence)
                    if len(insights) >= 5:
                        break
            if len(insights) >= 5:
                break

        # Identify specialist contributions
        specialists = [r for r in responses if r.specialty]
        specialist_domains = list(set(r.specialty for r in specialists if r.specialty))

        # Collect referenced tenets
        all_tenet_refs = set()
        for r in responses:
            all_tenet_refs.update(r.tenet_refs)

        # Build response
        parts = []

        # Confidence indicator
        if avg_confidence >= 0.7:
            parts.append(f"The swarm speaks with {int(avg_confidence * 100)}% confidence:")
        elif avg_confidence >= 0.5:
            parts.append("The swarm offers this perspective:")
        else:
            parts.append("The swarm is uncertain, but offers:")

        # Main insights
        if insights:
            parts.append(" ".join(insights[:3]))

        # Specialist note
        if specialist_domains:
            domains_str = ", ".join(specialist_domains[:3])
            parts.append(f"(Expertise contributed from: {domains_str})")

        # Tenet foundation
        if all_tenet_refs:
            parts.append(f"This response is grounded in {len(all_tenet_refs)} shared tenets.")

        # Metadata
        parts.append(f"[{len(responses)} agents deliberated]")

        return " ".join(parts)


async def create_deliberation_service(
    redis_url: str,
    memory: MemoryBackend | None = None,
) -> DeliberationService:
    """Factory function to create a configured DeliberationService."""
    import redis.asyncio as aioredis

    client = aioredis.from_url(redis_url, decode_responses=True)
    await client.ping()

    # If no memory provided, create Redis-backed memory
    if memory is None:
        from .memory import RedisMemory
        from .security import AuditLogger
        from pathlib import Path

        audit = AuditLogger(Path("data/logs"))
        memory = RedisMemory(client, audit)

    return DeliberationService(
        redis_client=client,
        memory=memory,
    )
