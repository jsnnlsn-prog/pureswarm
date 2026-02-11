"""Community chronicle — historical events that inform agent reasoning.

The Chronicle tracks significant community events (births, prophecies, consensus
milestones) that agents can reference when making decisions. Unlike tenets (which
are voted beliefs), chronicle events are factual records of what happened.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .models import ChronicleEvent, ChronicleCategory

logger = logging.getLogger("pureswarm.chronicle")

# Maximum recent events to keep (older ones are dropped)
MAX_RECENT_EVENTS = 100


class Chronicle:
    """File-backed community history store with event categorization."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._chronicle_file = self._data_dir / "chronicle.json"
        self._lock = asyncio.Lock()

        # Initialize empty chronicle file if it doesn't exist
        if not self._chronicle_file.exists():
            self._write_json({"recent_events": [], "milestones": []})

    # ------------------------------------------------------------------
    # Public read (any agent may call)
    # ------------------------------------------------------------------

    async def read_recent(self, limit: int = 20) -> list[ChronicleEvent]:
        """Read the most recent chronicle events.

        Args:
            limit: Maximum number of recent events to return (default 20)

        Returns:
            List of recent ChronicleEvent objects, newest first
        """
        raw = await asyncio.to_thread(self._read_json)
        recent = raw.get("recent_events", [])
        # Return newest first, limited
        return [ChronicleEvent.model_validate(e) for e in recent[-limit:]][::-1]

    async def read_milestones(self) -> list[ChronicleEvent]:
        """Read all milestone events (permanent significant events).

        Returns:
            List of milestone ChronicleEvent objects
        """
        raw = await asyncio.to_thread(self._read_json)
        milestones = raw.get("milestones", [])
        return [ChronicleEvent.model_validate(e) for e in milestones]

    async def read_all(self) -> dict[str, list[ChronicleEvent]]:
        """Read all chronicle data (recent events + milestones).

        Returns:
            Dict with 'recent_events' and 'milestones' keys
        """
        raw = await asyncio.to_thread(self._read_json)
        return {
            "recent_events": [ChronicleEvent.model_validate(e) for e in raw.get("recent_events", [])],
            "milestones": [ChronicleEvent.model_validate(e) for e in raw.get("milestones", [])]
        }

    # ------------------------------------------------------------------
    # Public write (simulation system only)
    # ------------------------------------------------------------------

    async def record_event(
        self,
        category: ChronicleCategory | str,
        text: str,
        round_number: int,
        metadata: dict | None = None,
        is_milestone: bool = False,
    ) -> None:
        """Record a new chronicle event.

        Args:
            category: Event category (growth, prophecy, consensus, etc.)
            text: Human-readable description of the event
            round_number: Simulation round when event occurred
            metadata: Additional structured data about the event
            is_milestone: If True, event is permanent; otherwise subject to rolling window
        """
        if isinstance(category, str):
            category = ChronicleCategory(category)

        event = ChronicleEvent(
            round_number=round_number,
            category=category,
            text=text,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
        )

        async with self._lock:
            raw = await asyncio.to_thread(self._read_json)

            if is_milestone:
                # Add to permanent milestones
                raw["milestones"].append(event.model_dump(mode="json"))
                logger.info("Chronicle milestone: %s", text)
            else:
                # Add to recent events (with rolling window)
                raw["recent_events"].append(event.model_dump(mode="json"))

                # Enforce rolling window (keep only most recent MAX_RECENT_EVENTS)
                if len(raw["recent_events"]) > MAX_RECENT_EVENTS:
                    raw["recent_events"] = raw["recent_events"][-MAX_RECENT_EVENTS:]

                logger.info("Chronicle event [%s]: %s", category.value, text)

            await asyncio.to_thread(self._write_json, raw)

    # ------------------------------------------------------------------
    # Reset (for simulation reruns)
    # ------------------------------------------------------------------

    async def reset(self) -> None:
        """Load existing chronicle instead of wiping it.

        This preserves community history across simulation runs,
        parallel to how tenets now persist.
        """
        # No-op: chronicle persists across runs
        # Initial empty state is handled by __init__
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_json(self) -> dict:
        """Read chronicle data from file."""
        if not self._chronicle_file.exists():
            return {"recent_events": [], "milestones": []}
        with open(self._chronicle_file, encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, data: dict) -> None:
        """Write chronicle data to file."""
        with open(self._chronicle_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
