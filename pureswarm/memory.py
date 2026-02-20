"""Consensus-gated shared memory store.

Tenets (shared beliefs) can be stored as:
  - JSON file (local development, default)
  - Redis/Dynomite (distributed deployment)

Writes are ONLY permitted through the consensus protocol — direct
mutation is blocked. Every write archives the previous version for
auditability.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from .models import AuditEntry, Tenet
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
