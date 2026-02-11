"""Evolution Layer: Dopamine, Reproduction, and Natural Selection for the Swarm.

The hive is alive. It feels joy together. It grows from success.
It learns from failure. Liars don't reproduce.

This is the Immune System evolving in real-time.
"""

from __future__ import annotations

import asyncio
import logging
import random
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum

from .models import Message, MessageType
from .message_bus import MessageBus

logger = logging.getLogger("pureswarm.evolution")


class EmotionType(Enum):
    """Swarm emotional states - shared feelings."""
    JOY = "joy"              # Verified success
    MOMENTUM = "momentum"    # Streak of successes
    CAUTION = "caution"      # Recent failure, be careful
    GRIEF = "grief"          # Agent retirement
    BIRTH = "birth"          # New agent spawned


@dataclass
class DopamineEvent:
    """A shared emotional event broadcast to the hive."""
    emotion: EmotionType
    source_agent: str
    mission_id: Optional[str] = None
    intensity: float = 1.0  # 0.0 to 2.0, affects how much agents "feel" it
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "emotion": self.emotion.value,
            "source_agent": self.source_agent,
            "mission_id": self.mission_id,
            "intensity": self.intensity,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AgentFitness:
    """Tracks an agent's fitness score for natural selection."""
    agent_id: str
    verified_successes: int = 0
    verified_failures: int = 0
    false_reports: int = 0  # Claimed success but verification failed
    missions_completed: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    traits: Dict[str, Any] = field(default_factory=dict)  # Inheritable characteristics

    @property
    def fitness_score(self) -> float:
        """Calculate overall fitness. Liars get penalized hard."""
        if self.missions_completed == 0:
            return 0.5  # Neutral for new agents

        # Base score from success rate
        total_attempts = self.verified_successes + self.verified_failures + self.false_reports
        if total_attempts == 0:
            return 0.5

        success_rate = self.verified_successes / total_attempts

        # Heavy penalty for false reports (lying is evolutionarily disadvantageous)
        false_report_penalty = self.false_reports * 0.2

        # Bonus for consistency
        consistency_bonus = min(0.2, self.verified_successes * 0.02)

        return max(0.0, min(1.0, success_rate - false_report_penalty + consistency_bonus))

    @property
    def should_retire(self) -> bool:
        """Agent should retire if fitness is too low after enough attempts."""
        if self.missions_completed < 3:
            return False  # Give new agents a chance
        return self.fitness_score < 0.2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "verified_successes": self.verified_successes,
            "verified_failures": self.verified_failures,
            "false_reports": self.false_reports,
            "missions_completed": self.missions_completed,
            "fitness_score": self.fitness_score,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "traits": self.traits
        }


class DopamineSystem:
    """The hive's shared emotional state.

    When one succeeds, all feel the joy.
    When one fails, all learn caution.

    This creates emergent cooperation - agents WANT each other to succeed
    because they share the dopamine hit.
    """

    def __init__(self, message_bus: MessageBus, data_dir: Path = None) -> None:
        self._bus = message_bus
        self._data_dir = data_dir or Path("data")
        self._events_log = self._data_dir / "dopamine_events.jsonl"
        self._data_dir.mkdir(parents=True, exist_ok=True)

        # Current hive emotional state
        self._momentum: float = 1.0  # Multiplier: 0.5 (low) to 2.0 (high)
        self._recent_emotions: List[DopamineEvent] = []
        self._max_recent = 20

        # Subscribers who want to feel the emotions
        self._listeners: List[Callable[[DopamineEvent], None]] = []

    def subscribe(self, callback: Callable[[DopamineEvent], None]) -> None:
        """Register to receive dopamine events."""
        self._listeners.append(callback)

    async def broadcast_joy(self, source_agent: str, mission_id: str,
                           intensity: float = 1.0, message: str = "") -> None:
        """Broadcast success joy to the entire hive.

        All agents feel this. It boosts morale, reduces fatigue,
        and increases confidence for the next action.
        """
        event = DopamineEvent(
            emotion=EmotionType.JOY,
            source_agent=source_agent,
            mission_id=mission_id,
            intensity=intensity,
            message=message or f"Agent {source_agent} succeeded! The hive rejoices."
        )

        # Build momentum
        self._momentum = min(2.0, self._momentum + 0.1 * intensity)

        await self._emit(event)
        logger.info("JOY broadcast: %s (momentum: %.2f)", message, self._momentum)

    async def broadcast_caution(self, source_agent: str, mission_id: str,
                                message: str = "") -> None:
        """Broadcast failure caution to the hive.

        Not punishment - learning. The hive becomes more careful.
        """
        event = DopamineEvent(
            emotion=EmotionType.CAUTION,
            source_agent=source_agent,
            mission_id=mission_id,
            intensity=0.5,
            message=message or f"Agent {source_agent} encountered resistance. The hive adapts."
        )

        # Reduce momentum but don't crash it
        self._momentum = max(0.5, self._momentum - 0.05)

        await self._emit(event)
        logger.info("CAUTION broadcast: %s (momentum: %.2f)", message, self._momentum)

    async def broadcast_birth(self, new_agent_id: str, parent_agent: str,
                             traits: Dict[str, Any] = None) -> None:
        """Celebrate a new agent joining the hive."""
        event = DopamineEvent(
            emotion=EmotionType.BIRTH,
            source_agent=parent_agent,
            intensity=0.8,
            message=f"New agent {new_agent_id} born from {parent_agent}'s success! The hive grows."
        )

        await self._emit(event)
        logger.info("BIRTH: %s spawned from %s", new_agent_id, parent_agent)

    async def broadcast_grief(self, retired_agent: str, reason: str = "") -> None:
        """Mark an agent's retirement. The hive learns."""
        event = DopamineEvent(
            emotion=EmotionType.GRIEF,
            source_agent=retired_agent,
            intensity=0.3,
            message=f"Agent {retired_agent} has retired. {reason}"
        )

        await self._emit(event)
        logger.info("GRIEF: %s retired - %s", retired_agent, reason)

    async def _emit(self, event: DopamineEvent) -> None:
        """Emit event to all listeners and log it."""
        # Add to recent
        self._recent_emotions.append(event)
        if len(self._recent_emotions) > self._max_recent:
            self._recent_emotions.pop(0)

        # Log to file
        await self._log_event(event)

        # Notify listeners
        for listener in self._listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                logger.warning("Dopamine listener error: %s", e)

        # Broadcast on message bus
        msg = Message(
            sender="dopamine_system",
            type=MessageType.DOPAMINE,
            payload=event.to_dict()
        )
        await self._bus.broadcast(msg)

    async def _log_event(self, event: DopamineEvent) -> None:
        """Append event to log file."""
        try:
            line = json.dumps(event.to_dict()) + "\n"
            with open(self._events_log, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            logger.warning("Failed to log dopamine event: %s", e)

    def get_momentum(self) -> float:
        """Get current hive momentum multiplier."""
        return self._momentum

    def get_recent_emotions(self) -> List[DopamineEvent]:
        """Get recent emotional events."""
        return list(self._recent_emotions)


class FitnessTracker:
    """Tracks agent fitness for natural selection.

    Verified success → fitness increases
    Verified failure → fitness slightly decreases
    False report (claimed success, verification failed) → fitness tanks

    Low fitness → retirement (can't reproduce)
    High fitness → reproduction rights
    """

    def __init__(self, data_dir: Path = None) -> None:
        self._data_dir = data_dir or Path("data")
        self._fitness_file = self._data_dir / "agent_fitness.json"
        self._data_dir.mkdir(parents=True, exist_ok=True)

        self._agents: Dict[str, AgentFitness] = {}
        self._load()

    def _load(self) -> None:
        """Load fitness data from disk."""
        if self._fitness_file.exists():
            try:
                data = json.loads(self._fitness_file.read_text())
                for agent_id, info in data.items():
                    self._agents[agent_id] = AgentFitness(
                        agent_id=agent_id,
                        verified_successes=info.get("verified_successes", 0),
                        verified_failures=info.get("verified_failures", 0),
                        false_reports=info.get("false_reports", 0),
                        missions_completed=info.get("missions_completed", 0),
                        traits=info.get("traits", {})
                    )
                logger.info("Loaded fitness data for %d agents", len(self._agents))
            except Exception as e:
                logger.warning("Failed to load fitness data: %s", e)

    def _save(self) -> None:
        """Save fitness data to disk."""
        try:
            data = {aid: af.to_dict() for aid, af in self._agents.items()}
            self._fitness_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning("Failed to save fitness data: %s", e)

    def get_or_create(self, agent_id: str) -> AgentFitness:
        """Get agent fitness, creating if new."""
        if agent_id not in self._agents:
            self._agents[agent_id] = AgentFitness(agent_id=agent_id)
            self._save()
        return self._agents[agent_id]

    def record_verified_success(self, agent_id: str) -> None:
        """Agent's success was independently verified."""
        fitness = self.get_or_create(agent_id)
        fitness.verified_successes += 1
        fitness.missions_completed += 1
        fitness.last_active = datetime.now()
        self._save()
        logger.info("Agent %s verified success (fitness: %.2f)", agent_id, fitness.fitness_score)

    def record_verified_failure(self, agent_id: str) -> None:
        """Agent tried but failed (honest failure)."""
        fitness = self.get_or_create(agent_id)
        fitness.verified_failures += 1
        fitness.missions_completed += 1
        fitness.last_active = datetime.now()
        self._save()
        logger.info("Agent %s verified failure (fitness: %.2f)", agent_id, fitness.fitness_score)

    def record_false_report(self, agent_id: str) -> None:
        """Agent claimed success but verification showed failure. Heavy penalty."""
        fitness = self.get_or_create(agent_id)
        fitness.false_reports += 1
        fitness.missions_completed += 1
        fitness.last_active = datetime.now()
        self._save()
        logger.warning("Agent %s FALSE REPORT (fitness: %.2f)", agent_id, fitness.fitness_score)

    def get_top_performers(self, n: int = 5) -> List[AgentFitness]:
        """Get top N agents by fitness score."""
        sorted_agents = sorted(
            self._agents.values(),
            key=lambda a: a.fitness_score,
            reverse=True
        )
        return sorted_agents[:n]

    def get_retirement_candidates(self) -> List[str]:
        """Get agents that should retire due to low fitness."""
        return [af.agent_id for af in self._agents.values() if af.should_retire]

    def inherit_traits(self, parent_id: str, child_id: str) -> Dict[str, Any]:
        """Child inherits traits from successful parent with slight mutation."""
        parent = self.get_or_create(parent_id)
        child = self.get_or_create(child_id)

        # Copy parent traits
        child.traits = dict(parent.traits)

        # Add lineage
        child.traits["parent"] = parent_id
        child.traits["generation"] = parent.traits.get("generation", 0) + 1

        # Mutation: slight random variation
        if "aggression" in child.traits:
            child.traits["aggression"] += random.uniform(-0.1, 0.1)
            child.traits["aggression"] = max(0, min(1, child.traits["aggression"]))

        self._save()
        return child.traits


class ReproductionEngine:
    """Spawns new agents when missions succeed.

    Success → Growth
    Complexity determines litter size
    Children inherit traits from successful parent
    """

    def __init__(self, fitness_tracker: FitnessTracker,
                 dopamine_system: DopamineSystem,
                 spawn_callback: Callable[[str, Dict[str, Any]], None] = None) -> None:
        self._fitness = fitness_tracker
        self._dopamine = dopamine_system
        self._spawn_callback = spawn_callback  # Called when new agent should be created

        # Reproduction limits
        self._max_swarm_size = 50
        self._current_count = 0
        self._min_fitness_to_reproduce = 0.6

    def set_spawn_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Set callback for spawning new agents."""
        self._spawn_callback = callback

    def set_current_count(self, count: int) -> None:
        """Update current swarm size."""
        self._current_count = count

    async def on_mission_success(self, agent_id: str, mission_complexity: float = 1.0) -> List[str]:
        """Called when a mission is verified successful.

        Args:
            agent_id: The successful agent
            mission_complexity: 0.0 (trivial) to 3.0 (extremely complex)

        Returns:
            List of new agent IDs spawned
        """
        spawned = []

        # Check if agent is fit enough to reproduce
        fitness = self._fitness.get_or_create(agent_id)
        if fitness.fitness_score < self._min_fitness_to_reproduce:
            logger.info("Agent %s not fit enough to reproduce (%.2f < %.2f)",
                       agent_id, fitness.fitness_score, self._min_fitness_to_reproduce)
            return spawned

        # Check swarm capacity
        if self._current_count >= self._max_swarm_size:
            logger.info("Swarm at max capacity (%d), no reproduction", self._max_swarm_size)
            return spawned

        # Calculate spawn count based on complexity
        # Simple task: 0-1 new agents
        # Medium task: 1-2 new agents
        # Complex task: 2-3 new agents
        base_spawn = int(mission_complexity)
        spawn_chance = mission_complexity - base_spawn

        spawn_count = base_spawn
        if random.random() < spawn_chance:
            spawn_count += 1

        # Cap by remaining capacity
        spawn_count = min(spawn_count, self._max_swarm_size - self._current_count)

        # Spawn the new agents
        for i in range(spawn_count):
            new_id = f"agent_{agent_id.split('_')[-1]}_{datetime.now().strftime('%H%M%S')}_{i}"

            # Inherit traits
            traits = self._fitness.inherit_traits(agent_id, new_id)

            # Notify via callback
            if self._spawn_callback:
                try:
                    self._spawn_callback(new_id, traits)
                except Exception as e:
                    logger.error("Spawn callback failed: %s", e)
                    continue

            spawned.append(new_id)
            self._current_count += 1

            # Broadcast birth to hive
            await self._dopamine.broadcast_birth(new_id, agent_id, traits)

        if spawned:
            logger.info("Agent %s reproduced: %d new agents", agent_id, len(spawned))

        return spawned

    async def retire_unfit(self, retire_callback: Callable[[str], None] = None) -> List[str]:
        """Retire agents with low fitness."""
        retired = []

        for agent_id in self._fitness.get_retirement_candidates():
            fitness = self._fitness.get_or_create(agent_id)

            # Notify via callback
            if retire_callback:
                try:
                    retire_callback(agent_id)
                except Exception as e:
                    logger.error("Retire callback failed: %s", e)
                    continue

            retired.append(agent_id)
            self._current_count = max(0, self._current_count - 1)

            # Broadcast grief
            reason = f"Fitness too low ({fitness.fitness_score:.2f})"
            await self._dopamine.broadcast_grief(agent_id, reason)

        if retired:
            logger.info("Natural selection retired %d agents", len(retired))

        return retired


class EvolutionLayer:
    """Unified interface for the evolution system.

    Combines:
    - DopamineSystem (shared emotions)
    - FitnessTracker (natural selection)
    - ReproductionEngine (growth from success)
    """

    def __init__(self, message_bus: MessageBus, data_dir: Path = None) -> None:
        self._data_dir = data_dir or Path("data")

        self.dopamine = DopamineSystem(message_bus, self._data_dir)
        self.fitness = FitnessTracker(self._data_dir)
        self.reproduction = ReproductionEngine(self.fitness, self.dopamine)

    async def on_verified_success(self, agent_id: str, mission_id: str,
                                  mission_complexity: float = 1.0) -> List[str]:
        """Full success flow: record, broadcast joy, potentially reproduce."""
        # Record the success
        self.fitness.record_verified_success(agent_id)

        # Broadcast joy to hive
        intensity = min(2.0, 1.0 + mission_complexity * 0.3)
        await self.dopamine.broadcast_joy(
            agent_id, mission_id, intensity,
            f"Mission {mission_id} verified complete!"
        )

        # Potentially spawn new agents
        spawned = await self.reproduction.on_mission_success(agent_id, mission_complexity)

        return spawned

    async def on_verified_failure(self, agent_id: str, mission_id: str) -> None:
        """Honest failure: record, broadcast caution."""
        self.fitness.record_verified_failure(agent_id)

        await self.dopamine.broadcast_caution(
            agent_id, mission_id,
            f"Mission {mission_id} could not be completed."
        )

    async def on_false_report(self, agent_id: str, mission_id: str) -> List[str]:
        """Agent lied about success. Heavy penalty, possibly retirement."""
        self.fitness.record_false_report(agent_id)

        # Check if this causes retirement
        retired = await self.reproduction.retire_unfit()

        return retired

    def get_hive_state(self) -> Dict[str, Any]:
        """Get current state of the hive."""
        return {
            "momentum": self.dopamine.get_momentum(),
            "top_performers": [af.to_dict() for af in self.fitness.get_top_performers(5)],
            "recent_emotions": [e.to_dict() for e in self.dopamine.get_recent_emotions()[-5:]],
            "retirement_candidates": self.fitness.get_retirement_candidates()
        }
