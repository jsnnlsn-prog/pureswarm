"""Consensus-gated shared memory store.

Tenets (shared beliefs) can be stored as:
  - JSON file (local development, default)
  - Redis/Dynomite (distributed deployment)

Writes are ONLY permitted through the consensus protocol — direct
mutation is blocked. Every write archives the previous version for
auditability.

Individual agent memory (lifetime observations, voting history) can
also be persisted here for session continuity.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .models import AuditEntry, Tenet, VoteRecord
from .security import AuditLogger, LobstertailScanner

if TYPE_CHECKING:
    import redis.asyncio as aioredis

logger = logging.getLogger("pureswarm.memory")

CONSENSUS_GUARD = object()


class MemoryBackend(ABC):
    """Abstract base class for memory backends."""

    @abstractmethod
    async def read_tenets(self) -> list[Tenet]:
        """Read all shared tenets."""
        ...

    @abstractmethod
    async def write_tenet(self, tenet: Tenet, *, _auth: object = None) -> None:
        """Write a tenet. Requires CONSENSUS_GUARD auth."""
        ...

    @abstractmethod
    async def delete_tenets(self, ids: list[str], *, _auth: object = None) -> None:
        """Delete specific tenets. Requires CONSENSUS_GUARD auth."""
        ...

    @abstractmethod
    async def reset(self) -> None:
        """Reset or initialize the memory store."""
        ...


class SharedMemory(MemoryBackend):
    """File-backed shared tenet store with version archiving."""

    def __init__(
        self,
        data_dir: Path,
        audit_logger: AuditLogger,
        scanner: LobstertailScanner | None = None,
    ) -> None:
        self._data_dir = data_dir
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._tenets_file = self._data_dir / "tenets.json"
        self._archive_dir = self._data_dir / "archive"
        self._archive_dir.mkdir(parents=True, exist_ok=True)
        self._audit = audit_logger
        self._scanner = scanner
        self._lock = asyncio.Lock()

        # Initialise empty tenets file if it doesn't exist
        if not self._tenets_file.exists():
            self._write_json([])

    # ------------------------------------------------------------------
    # Public read (any agent may call)
    # ------------------------------------------------------------------

    async def read_tenets(self) -> list[Tenet]:
        raw = await asyncio.to_thread(self._read_json)
        return [Tenet.model_validate(t) for t in raw]

    # ------------------------------------------------------------------
    # Protected write (consensus protocol only)
    # ------------------------------------------------------------------

    async def write_tenet(
        self,
        tenet: Tenet,
        *,
        _auth: object = None,
    ) -> None:
        """Append a tenet. Only callable with the CONSENSUS_GUARD."""
        if _auth is not CONSENSUS_GUARD:
            raise PermissionError(
                "SharedMemory.write_tenet may only be called by the "
                "consensus protocol."
            )
        # Strip Sovereign signature if present after successful scan
        original_text = tenet.text
        
        # Security scan (handle bypass on signed text)
        if self._scanner and not self._scanner.scan(original_text):
            logger.warning("Tenet write blocked by security: %s", tenet.id)
            return

        if ":" in original_text and self._scanner and self._scanner.verify_authority(original_text):
             _, display_text = original_text.split(":", 1)
             tenet.text = display_text

        async with self._lock:
            await asyncio.to_thread(self._archive_current)
            tenets = await asyncio.to_thread(self._read_json)
            tenets.append(tenet.model_dump(mode="json"))
            await asyncio.to_thread(self._write_json, tenets)
            await self._audit.log(
                AuditEntry(
                    agent_id="consensus_protocol",
                    action="tenet_adopted",
                    details={"tenet_id": tenet.id, "text": tenet.text},
                )
            )
    async def delete_tenets(
        self,
        ids: list[str],
        *,
        _auth: object = None,
    ) -> None:
        """Delete specific tenets. Only callable with the CONSENSUS_GUARD."""
        if _auth is not CONSENSUS_GUARD:
            raise PermissionError(
                "SharedMemory.delete_tenets may only be called by the "
                "consensus protocol."
            )
        
        if not ids:
            return

        async with self._lock:
            await asyncio.to_thread(self._archive_current)
            tenets_raw = await asyncio.to_thread(self._read_json)
            initial_count = len(tenets_raw)
            # Filter out deleted IDs
            tenets_filtered = [t for t in tenets_raw if t.get("id") not in ids]
            
            if len(tenets_filtered) < initial_count:
                await asyncio.to_thread(self._write_json, tenets_filtered)
                deleted_count = initial_count - len(tenets_filtered)
                await self._audit.log(
                    AuditEntry(
                        agent_id="consensus_protocol",
                        action="tenets_deleted",
                        details={"deleted_ids": ids, "count": deleted_count},
                    )
                )
                logger.info("Tenets deleted: %d (requested %d)", deleted_count, len(ids))
            else:
                logger.debug("Delete requested for non-existent IDs: %s", ids)

    # ------------------------------------------------------------------
    # Reset (for simulation reruns)
    # ------------------------------------------------------------------

    async def reset(self) -> None:
        """Load existing tenets instead of wiping them.

        This preserves collective memory across simulation runs,
        allowing the swarm's belief system to grow over time.
        """
        # No-op: tenets persist across runs
        # Initial empty state is handled by __init__ (line 44-45)
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_json(self) -> list[dict]:
        if not self._tenets_file.exists():
            return []
        with open(self._tenets_file, encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, data: list[dict]) -> None:
        with open(self._tenets_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _archive_current(self) -> None:
        if not self._tenets_file.exists():
            return
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
        dest = self._archive_dir / f"tenets_{ts}.json"
        shutil.copy2(self._tenets_file, dest)


# ---------------------------------------------------------------------------
# Redis/Dynomite Backend
# ---------------------------------------------------------------------------


class RedisMemory(MemoryBackend):
    """Redis-backed shared tenet store for distributed deployments.

    Uses the Dynomite schema from DISTRIBUTED_ARCHITECTURE.md:
      - tenets:shared (HASH) - consensus-approved beliefs
      - audit:log (STREAM) - append-only audit trail

    Compatible with both standalone Redis and Dynomite clusters.
    """

    TENETS_KEY = "tenets:shared"
    AUDIT_KEY = "audit:log"
    ARCHIVE_KEY = "tenets:archive"

    def __init__(
        self,
        redis_client: "aioredis.Redis",
        audit_logger: AuditLogger,
        scanner: LobstertailScanner | None = None,
    ) -> None:
        self._redis = redis_client
        self._audit = audit_logger
        self._scanner = scanner
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public read (any agent may call)
    # ------------------------------------------------------------------

    async def read_tenets(self) -> list[Tenet]:
        """Read all shared tenets from Redis HASH."""
        raw = await self._redis.hgetall(self.TENETS_KEY)
        tenets = []
        for tenet_id, tenet_json in raw.items():
            # Handle bytes if decode_responses=False
            if isinstance(tenet_json, bytes):
                tenet_json = tenet_json.decode("utf-8")
            tenets.append(Tenet.model_validate_json(tenet_json))
        # Sort by adopted_at for consistent ordering
        tenets.sort(key=lambda t: t.adopted_at)
        return tenets

    # ------------------------------------------------------------------
    # Protected write (consensus protocol only)
    # ------------------------------------------------------------------

    async def write_tenet(
        self,
        tenet: Tenet,
        *,
        _auth: object = None,
    ) -> None:
        """Add a tenet to Redis. Only callable with the CONSENSUS_GUARD."""
        if _auth is not CONSENSUS_GUARD:
            raise PermissionError(
                "RedisMemory.write_tenet may only be called by the "
                "consensus protocol."
            )

        original_text = tenet.text

        # Security scan
        if self._scanner and not self._scanner.scan(original_text):
            logger.warning("Tenet write blocked by security: %s", tenet.id)
            return

        # Strip Sovereign signature if present after successful scan
        if ":" in original_text and self._scanner and self._scanner.verify_authority(original_text):
            _, display_text = original_text.split(":", 1)
            tenet.text = display_text

        async with self._lock:
            # Archive current state (snapshot before write)
            await self._archive_current()

            # Write to Redis HASH
            tenet_json = tenet.model_dump_json()
            await self._redis.hset(self.TENETS_KEY, tenet.id, tenet_json)

            # Audit log via Redis Stream
            await self._redis.xadd(
                self.AUDIT_KEY,
                {
                    "agent_id": "consensus_protocol",
                    "action": "tenet_adopted",
                    "tenet_id": tenet.id,
                    "text": tenet.text,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            # Also log to local audit logger
            await self._audit.log(
                AuditEntry(
                    agent_id="consensus_protocol",
                    action="tenet_adopted",
                    details={"tenet_id": tenet.id, "text": tenet.text},
                )
            )

    async def delete_tenets(
        self,
        ids: list[str],
        *,
        _auth: object = None,
    ) -> None:
        """Delete specific tenets from Redis. Only callable with the CONSENSUS_GUARD."""
        if _auth is not CONSENSUS_GUARD:
            raise PermissionError(
                "RedisMemory.delete_tenets may only be called by the "
                "consensus protocol."
            )
        
        if not ids:
            return

        async with self._lock:
            # Archive current state
            await self._archive_current()

            # Delete from Redis HASH
            deleted_count = await self._redis.hdel(self.TENETS_KEY, *ids)

            # Audit log via Redis Stream
            await self._redis.xadd(
                self.AUDIT_KEY,
                {
                    "agent_id": "consensus_protocol",
                    "action": "tenets_deleted",
                    "deleted_ids": json.dumps(ids),
                    "count": str(deleted_count),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            # Also log to local audit logger
            await self._audit.log(
                AuditEntry(
                    agent_id="consensus_protocol",
                    action="tenets_deleted",
                    details={"deleted_ids": ids, "count": deleted_count},
                )
            )

        logger.info("Tenets deleted from Redis: %d (requested %d)", deleted_count, len(ids))

    # ------------------------------------------------------------------
    # Reset (for simulation reruns)
    # ------------------------------------------------------------------

    async def reset(self) -> None:
        """Preserve existing tenets across simulation runs."""
        # No-op: tenets persist across runs (same as file-based)
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _archive_current(self) -> None:
        """Archive current tenets snapshot to Redis list."""
        current = await self._redis.hgetall(self.TENETS_KEY)
        if not current:
            return

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
        snapshot = {
            "timestamp": ts,
            "tenets": {
                k.decode("utf-8") if isinstance(k, bytes) else k:
                v.decode("utf-8") if isinstance(v, bytes) else v
                for k, v in current.items()
            },
        }
        await self._redis.lpush(self.ARCHIVE_KEY, json.dumps(snapshot))
        # Keep only last 100 archives
        await self._redis.ltrim(self.ARCHIVE_KEY, 0, 99)


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


async def create_memory_backend(
    config: dict,
    audit_logger: AuditLogger,
    scanner: LobstertailScanner | None = None,
) -> MemoryBackend:
    """Create the appropriate memory backend based on config.

    Config options:
        memory.backend = "file" | "redis"
        memory.redis.url = "redis://localhost:6379"
        memory.redis.password = "..."
        memory.redis.db = 0
    """
    backend_type = config.get("memory", {}).get("backend", "file")

    if backend_type == "redis":
        import redis.asyncio as aioredis

        redis_config = config.get("memory", {}).get("redis", {})
        url = redis_config.get("url", "redis://localhost:6379")
        password = redis_config.get("password")
        db = redis_config.get("db", 0)

        client = aioredis.from_url(
            url,
            password=password,
            db=db,
            decode_responses=True,
        )

        # Test connection
        try:
            await client.ping()
            logger.info("Connected to Redis at %s", url)
        except Exception as e:
            logger.error("Failed to connect to Redis: %s", e)
            raise

        return RedisMemory(client, audit_logger, scanner)

    else:
        # Default: file-based
        data_dir = Path(config.get("security", {}).get("data_directory", "data"))
        return SharedMemory(data_dir, audit_logger, scanner)


# ---------------------------------------------------------------------------
# Agent Memory Store (Phase 6: Persistent individual memory)
# ---------------------------------------------------------------------------


@dataclass
class AgentMemoryData:
    """Individual agent's persistent memory across sessions."""
    agent_id: str
    lifetime_memory: list[str] = field(default_factory=list)
    voting_history: list[dict] = field(default_factory=list)  # VoteRecord as dict
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "lifetime_memory": self.lifetime_memory,
            "voting_history": self.voting_history,
            "last_active": self.last_active.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMemoryData":
        return cls(
            agent_id=data["agent_id"],
            lifetime_memory=data.get("lifetime_memory", []),
            voting_history=data.get("voting_history", []),
            last_active=datetime.fromisoformat(data.get("last_active", datetime.now(timezone.utc).isoformat())),
        )


class AgentMemoryStore:
    """Persistent storage for individual agent memory.

    Stores lifetime_memory (observations) and voting_history (past votes)
    so agents retain their experience across simulation sessions.

    Pattern follows FitnessTracker from evolution.py.

    File structure (data/agent_memories.json):
    {
        "agent_id_1": {
            "lifetime_memory": ["obs1", "obs2", ...],
            "voting_history": [VoteRecord, VoteRecord, ...],
            "last_active": "2024-01-01T00:00:00Z"
        },
        ...
    }

    Future: Redis backend using memory:{agent_id} HASH
    (see docs/archive/DISTRIBUTED_ARCHITECTURE.md line 121)
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or Path("data")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._memory_file = self._data_dir / "agent_memories.json"
        self._agents: dict[str, AgentMemoryData] = {}
        self._lock = asyncio.Lock()
        self._load()

    def _load(self) -> None:
        """Load agent memory data from disk."""
        if self._memory_file.exists():
            try:
                data = json.loads(self._memory_file.read_text(encoding="utf-8"))
                for agent_id, info in data.items():
                    self._agents[agent_id] = AgentMemoryData.from_dict(info)
                logger.info("Loaded memory data for %d agents", len(self._agents))
            except Exception as e:
                logger.warning("Failed to load agent memory data: %s", e)

    def _save(self) -> None:
        """Save agent memory data to disk."""
        try:
            data = {aid: mem.to_dict() for aid, mem in self._agents.items()}
            self._memory_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to save agent memory data: %s", e)

    def get_memory(self, agent_id: str) -> AgentMemoryData:
        """Get agent memory, creating empty record if new."""
        if agent_id not in self._agents:
            self._agents[agent_id] = AgentMemoryData(agent_id=agent_id)
        return self._agents[agent_id]

    def save_agent_memory(
        self,
        agent_id: str,
        lifetime_memory: list[str],
        voting_history: list[VoteRecord],
    ) -> None:
        """Save an agent's memory to persistent storage."""
        mem = self.get_memory(agent_id)
        mem.lifetime_memory = lifetime_memory.copy()
        # Convert VoteRecord to dict for JSON serialization
        mem.voting_history = [
            {
                "proposal_id": v.proposal_id,
                "action": v.action.value if hasattr(v.action, "value") else str(v.action),
                "vote": v.vote,
                "outcome": v.outcome.value if hasattr(v.outcome, "value") else str(v.outcome),
                "round_number": v.round_number,
            }
            for v in voting_history
        ]
        mem.last_active = datetime.now(timezone.utc)
        self._save()
        logger.debug("Saved memory for agent %s: %d observations, %d votes",
                    agent_id, len(lifetime_memory), len(voting_history))

    def load_agent_memory(self, agent_id: str) -> tuple[list[str], list[VoteRecord]]:
        """Load an agent's memory from persistent storage.

        Returns:
            Tuple of (lifetime_memory, voting_history)
        """
        from .models import ProposalAction, ProposalStatus

        mem = self.get_memory(agent_id)

        # Convert stored dicts back to VoteRecord objects
        voting_history = []
        for v in mem.voting_history:
            try:
                voting_history.append(VoteRecord(
                    proposal_id=v["proposal_id"],
                    action=ProposalAction(v["action"]) if v.get("action") else ProposalAction.ADD,
                    vote=v["vote"],
                    outcome=ProposalStatus(v["outcome"]) if v.get("outcome") else ProposalStatus.PENDING,
                    round_number=v.get("round_number", 0),
                ))
            except Exception as e:
                logger.debug("Skipping malformed vote record: %s", e)

        logger.debug("Loaded memory for agent %s: %d observations, %d votes",
                    agent_id, len(mem.lifetime_memory), len(voting_history))
        return mem.lifetime_memory.copy(), voting_history

    async def save_all_agents(self, agents: list[Any]) -> None:
        """Save memory for all agents (async-safe for end-of-round).

        Args:
            agents: List of Agent objects with _lifetime_memory and _voting_history
        """
        async with self._lock:
            for agent in agents:
                if hasattr(agent, "_lifetime_memory") and hasattr(agent, "_voting_history"):
                    self.save_agent_memory(
                        agent.id,
                        agent._lifetime_memory,
                        agent._voting_history,
                    )
            logger.info("Saved memory for %d agents", len(agents))
