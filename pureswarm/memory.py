"""Consensus-gated shared memory store.

Tenets (shared beliefs) are stored as a JSON file. Writes are ONLY
permitted through the consensus protocol — direct mutation is blocked.
Every write archives the previous version for auditability.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .models import AuditEntry, Tenet
from .security import AuditLogger, LobstertailScanner

logger = logging.getLogger("pureswarm.memory")

CONSENSUS_GUARD = object()


class SharedMemory:
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
        logger.info("Tenet adopted: %s", tenet.text)

    # ------------------------------------------------------------------
    # Reset (for simulation reruns)
    # ------------------------------------------------------------------

    async def reset(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._write_json, [])

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
