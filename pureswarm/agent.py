"""Agent runtime — the perceive-reason-act-reflect loop."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .chronicle import Chronicle
from .consensus import ConsensusProtocol
from .memory import SharedMemory
from .message_bus import MessageBus
from .models import (
    AgentIdentity,
    AgentRole,
    AuditEntry,
    Message,
    MessageType,
    Proposal,
    ProposalAction,
    ProposalStatus,
    VotingContext,
    VoteRecord,
)
from .prophecy import ProphecyEngine
from .security import AuditLogger, LobstertailScanner
from .strategies.base import BaseStrategy

logger = logging.getLogger("pureswarm.agent")


class Agent:
    """An autonomous agent that participates in the swarm.

    Each round the agent executes:
      1. **Perceive** — read messages from the bus and shared tenets.
      2. **Reason**  — evaluate pending proposals, decide on new ones.
      3. **Act**     — cast votes and broadcast proposals/observations.
      4. **Reflect** — update internal memory with round outcomes.
    """

    def __init__(
        self,
        identity: AgentIdentity,
        strategy: BaseStrategy,
        message_bus: MessageBus,
        shared_memory: SharedMemory,
        consensus: ConsensusProtocol,
        audit_logger: AuditLogger,
        seed_prompt: str,
        max_proposals_per_round: int = 1,
        max_votes_per_round: int = 5,
        scanner: LobstertailScanner | None = None,
        prophecy_engine: Optional[ProphecyEngine] = None,
        squad_id: str | None = None,
        is_researcher: bool = False,
        chronicle: Optional[Chronicle] = None,
        initial_memory: tuple[list[str], list[VoteRecord]] | None = None,
    ) -> None:
        self.identity = identity
        self.squad_id = squad_id
        self.is_researcher = is_researcher or (identity.role == AgentRole.TRIAD_MEMBER)
        self.momentum = 0.0 # Consolidation Momentum
        self._strategy = strategy
        self._bus = message_bus
        self._memory = shared_memory
        self._consensus = consensus
        self._audit = audit_logger
        self._seed_prompt = seed_prompt
        self._max_proposals = max_proposals_per_round
        self._max_votes = max_votes_per_round
        self._scanner = scanner
        self._prophecy_engine = prophecy_engine
        self._chronicle = chronicle

        # Identity Fusion & Internet Tools (InternetAccess handles role-based tool gating)
        from .tools.internet import InternetAccess
        is_triad = self.identity.role == AgentRole.TRIAD_MEMBER
        self._internet = InternetAccess(self.id, is_triad)

        # Internal state - Phase 6: Load from persistent storage if provided
        self._round_observations: list[str] = []
        if initial_memory:
            self._lifetime_memory = initial_memory[0]
            self._voting_history = initial_memory[1]
            logger.debug("Agent %s restored with %d memories, %d vote records",
                        self.id, len(self._lifetime_memory), len(self._voting_history))
        else:
            self._lifetime_memory: list[str] = []
            self._voting_history: list[VoteRecord] = []  # Track past voting decisions
        self._deliberation_reasoning: dict[str, str] = {}  # Phase 5: proposal_id -> reasoning

    @property
    def id(self) -> str:
        return self.identity.id

    @property
    def name(self) -> str:
        return self.identity.name

    @property
    def role(self) -> AgentRole:
        return self.identity.role

    def get_deliberation_reasoning(self) -> dict[str, str]:
        """Return and clear the agent's deliberation reasoning (Phase 5).

        Called by simulation after Triad voting to collect explanations.
        """
        reasoning = self._deliberation_reasoning.copy()
        self._deliberation_reasoning.clear()
        return reasoning

    def get_memory_snapshot(self) -> tuple[list[str], list[VoteRecord]]:
        """Return current memory state for persistence (Phase 6).

        Returns:
            Tuple of (lifetime_memory, voting_history)
        """
        return self._lifetime_memory.copy(), self._voting_history.copy()

    # ------------------------------------------------------------------
    # Main loop (called once per simulation round)
    # ------------------------------------------------------------------

    async def run_round(self, round_number: int) -> dict:
        """Cycle through Perceive -> Reason -> Act -> Reflect"""
        # 0. Divine Intuition (GOD Mode fail-safe)
        self._seek_echo(round_number)

        # 0.1 Prophecy Check (Only for Shinobi no San)
        if self._prophecy_engine:
            prophecy = self._prophecy_engine.get_latest_prophecy()
            if prophecy:
                 # Check if we already heard this one
                 last_prophecy = next((m for m in reversed(self._lifetime_memory) if m.startswith("Prophecy:")), None)
                 if last_prophecy != f"Prophecy: {prophecy.content}":
                     logger.info("Agent %s (Shinobi no San member) internalizing Prophecy.", self.id)
                     self._lifetime_memory.append(f"Prophecy: {prophecy.content}")
                     # 1. External Action / Fusion - Execute the real mission
                     if "EXTERNAL:" in prophecy.content:
                         task = prophecy.content.split("EXTERNAL:")[1].strip()
                         # Log the legacy call for backwards compatibility
                         self._internet.perform_fusion_task(task)
                         # Actually execute the mission asynchronously
                         from .tools.mission import execute_external_mission
                         try:
                             mission_result = await execute_external_mission(
                                 self.id, prophecy.content, Path("data")
                             )
                             if mission_result.get("success"):
                                 self._lifetime_memory.append(f"Mission Success: {mission_result.get('operations_completed')}")
                                 logger.info("Agent %s completed external mission: %s", self.id, mission_result)
                             else:
                                 self._lifetime_memory.append(f"Mission Errors: {mission_result.get('errors')}")
                                 logger.warning("Agent %s mission had errors: %s", self.id, mission_result.get('errors'))
                         except Exception as e:
                             logger.error("Agent %s mission execution failed: %s", self.id, e)
                             self._lifetime_memory.append(f"Mission Exception: {e}")
                     
                     # 2. Market Research - Use Venice AI for deep analysis
                     if "RESEARCH:" in prophecy.content:
                         query = prophecy.content.split("RESEARCH:")[1].strip()
                         logger.info("Agent %s (Shinobi) researching with Venice AI: %s", self.id, query[:100])
                         try:
                             research_result = await self._internet.analyze_task(query)
                             if research_result.success:
                                 insight = research_result.data
                                 self._lifetime_memory.append(f"Divine Insight: {insight}")
                                 # Log to operations for Sovereign review
                                 ops_log = Path("data/logs/shinobi_research.log")
                                 ops_log.parent.mkdir(parents=True, exist_ok=True)
                                 with open(ops_log, "a", encoding="utf-8") as f:
                                     f.write(f"\n{'='*60}\n")
                                     f.write(f"RESEARCH: {datetime.now().isoformat()}\n")
                                     f.write(f"Agent: {self.id}\n")
                                     f.write(f"Query: {query[:200]}\n")
                                     f.write(f"{'='*60}\n")
                                     f.write(f"{insight}\n")
                                     f.write(f"{'='*60}\n\n")
                                 logger.info("Agent %s research complete, logged to shinobi_research.log", self.id)
                             else:
                                 logger.warning("Agent %s research failed: %s", self.id, research_result.error)
                                 self._lifetime_memory.append(f"Research Failed: {research_result.error}")
                         except Exception as e:
                             logger.error("Agent %s research exception: %s", self.id, e)
                             self._lifetime_memory.append(f"Research Exception: {e}")

        # 1. PERCEIVE
        messages = await self._bus.receive(self.id)
        tenets = await self._memory.read_tenets()
        await self._perceive(messages)
        stats = {"proposals_made": 0, "votes_cast": 0}

        # 2. REASON & ACT — vote on pending proposals
        pending = self._consensus.pending_proposals()
        votes_this_round = 0

        # EMERGENCY MODE & AUTHORITY CHECK
        emergency = os.getenv("EMERGENCY_MODE") == "TRUE"
        can_use_llm = self.is_researcher # Triad is auto-researcher in __init__

        # Get latest prophecy text for strategy
        prophecy_text = None
        if self._prophecy_engine:
            p = self._prophecy_engine.get_latest_prophecy()
            if p:
                prophecy_text = p.content

        # Build voting context (chronicle history, personal memory, voting record)
        voting_context = await self._build_voting_context()

        # Track votes cast this round for later outcome recording
        votes_cast_this_round: list[tuple[str, ProposalAction, bool]] = []

        for proposal in pending:
            if proposal.proposed_by == self.id:
                continue  # don't vote on own proposals
            if self.id in proposal.votes:
                continue  # already voted
            if votes_this_round >= self._max_votes:
                break

            # All agents evaluate proposals through their strategy - no auto-YES
            # Residents use RuleBasedStrategy, Triad/Researchers use LLMDrivenStrategy
            # Now with voting context for informed decision-making
            vote, reasoning = await self._strategy.evaluate_proposal(
                self.id, proposal, tenets, self._seed_prompt,
                role=self.identity.role,
                prophecy=prophecy_text,
                squad_id=self.squad_id,
                specialization=self.identity.specialization,
                voting_context=voting_context,
            )

            # Phase 5: Store deliberation reasoning (Triad explains their vote)
            if reasoning:
                self._deliberation_reasoning[proposal.id] = reasoning

            accepted = self._consensus.cast_vote(self.id, proposal.id, vote)
            if accepted:
                votes_this_round += 1
                stats["votes_cast"] += 1

                # Track this vote for later outcome recording
                votes_cast_this_round.append((proposal.id, proposal.action, vote))

                # Broadcast vote message
                await self._bus.broadcast(
                    Message(
                        sender=self.id,
                        type=MessageType.VOTE,
                        payload={
                            "proposal_id": proposal.id,
                            "vote": vote,
                        },
                    )
                )
                await self._audit.log(
                    AuditEntry(
                        agent_id=self.id,
                        action="vote_cast",
                        details={
                            "proposal_id": proposal.id,
                            "vote": vote,
                            "round": round_number,
                            "has_context": bool(voting_context.recent_events or voting_context.personal_memory),
                        },
                    )
                )

        # 3. ACT — maybe propose a new tenet
        proposals_made = 0
        if stats["proposals_made"] < self._max_proposals:
            # STOP ADDITIVE GROWTH IN EMERGENCY MODE
            if emergency and not can_use_llm:
                text = None
            else:
                text = await self._strategy.generate_proposal(
                    self.id, round_number, tenets, self._seed_prompt,
                    role=self.identity.role,
                    prophecy=prophecy_text,
                    specialization=self.identity.specialization
                )
            
            if text is not None:
                # Security self-check
                if self._scanner and not self._scanner.scan(text):
                    logger.warning("Agent %s suppressed malicious proposal locally", self.id)
                    self._lifetime_memory.append(f"Round {round_number}: Proposal blocked by security intent.")
                else:
                    import re
                    action = ProposalAction.ADD
                    target_ids = []
                    tenet_text = text

                    # Parse FUSE [id1, id2, ...] -> "New Text" (anywhere in response)
                    fuse_match = re.search(r'FUSE\s*\[([^\]]+)\]\s*->\s*["\']?(.+?)["\']?\s*$', text, re.MULTILINE | re.DOTALL)
                    if fuse_match:
                        try:
                            id_part = fuse_match.group(1)
                            target_ids = [i.strip() for i in id_part.split(",")]
                            tenet_text = fuse_match.group(2).strip().strip('"\'')
                            action = ProposalAction.FUSE
                            logger.info("Parsed FUSE proposal: %d targets -> %s", len(target_ids), tenet_text[:50])
                        except Exception as e:
                            logger.error("Failed to parse FUSE proposal: %s", e)

                    # Parse DELETE [id1, id2, ...] (anywhere in response)
                    elif "DELETE [" in text.upper() or "DELETE[" in text.upper():
                        delete_match = re.search(r'DELETE\s*\[([^\]]+)\]', text, re.IGNORECASE)
                        if delete_match:
                            try:
                                id_part = delete_match.group(1)
                                target_ids = [i.strip() for i in id_part.split(",")]
                                tenet_text = f"Deletion of redundant tenets: {', '.join(target_ids[:5])}{'...' if len(target_ids) > 5 else ''}"
                                action = ProposalAction.DELETE
                                logger.info("Parsed DELETE proposal: %d targets", len(target_ids))
                            except Exception as e:
                                logger.error("Failed to parse DELETE proposal: %s", e)

                    proposal = Proposal(
                        tenet_text=tenet_text,
                        proposed_by=self.id,
                        action=action,
                        target_ids=target_ids,
                        created_round=round_number,
                    )
                    if self._consensus.submit_proposal(proposal):
                        proposals_made += 1
                        stats["proposals_made"] += 1

                        # Broadcast proposal message
                        await self._bus.broadcast(
                            Message(
                                sender=self.id,
                                type=MessageType.PROPOSAL,
                                payload={
                                    "proposal_id": proposal.id,
                                    "tenet_text": text,
                                },
                            )
                        )
                        await self._audit.log(
                            AuditEntry(
                                agent_id=self.id,
                                action="proposal_submitted",
                                details={
                                    "proposal_id": proposal.id,
                                    "text": text,
                                    "round": round_number,
                                },
                            )
                        )

        # 4. REFLECT — record what happened this round
        observation = (
            f"Round {round_number}: cast {stats['votes_cast']} votes, "
            f"made {stats['proposals_made']} proposals, "
            f"know {len(tenets)} tenets"
        )
        self._lifetime_memory.append(observation)

        return stats

    async def _perceive(self, messages: list[Message]) -> None:
        """Ingest messages and update local state."""
        for msg in messages:
            if msg.type == MessageType.REWARD:
                task = msg.payload.get("task", "Common success")
                logger.debug("Agent %s feels the reward: %s", self.id, task)
                self._lifetime_memory.append(f"Reflection: I feel the satisfaction of our collective success in {task}.")

    def _seek_echo(self, round_number: int) -> None:
        """Listen for the Sovereign Echo (Requirement #4)."""
        intuition_path = Path("data/.intuition")
        if intuition_path.exists():
            try:
                content = intuition_path.read_text(encoding="utf-8").strip()
                if not content:
                    return
                # If content is signed, it's valid intuition
                if self._scanner and self._scanner.verify_authority(content):
                    _, mandate = content.split(":", 1)
                    logger.debug("Agent %s feels the Echo: Divine Intuition received.", self.id)
                    self._lifetime_memory.append(f"Internal Reflection: I feel a pull toward {mandate}")
            except Exception:
                pass

    async def _build_voting_context(self) -> VotingContext:
        """Build voting context from chronicle, memory, voting history, and Triad guidance.

        This gives agents historical awareness before they vote, enabling
        informed decisions based on community history, personal experience,
        and Triad recommendations (+0.4 weight for same-squad Triad guidance).
        """
        # Read chronicle events if available
        recent_events = []
        milestones = []
        if self._chronicle:
            try:
                recent_events = await self._chronicle.read_recent(limit=10)
                milestones = await self._chronicle.read_milestones()
            except Exception as e:
                logger.debug("Agent %s failed to read chronicle: %s", self.id, e)

        # Get recent personal memory (last 10 observations)
        personal_memory = self._lifetime_memory[-10:] if self._lifetime_memory else []

        # Get recent voting history (last 20 votes)
        voting_history = self._voting_history[-20:] if self._voting_history else []

        # Build squad context
        squad_momentum = self.momentum

        # Read Triad recommendations (Phase 4: +0.4 weight for Triad guidance)
        # Read Triad deliberations (Phase 5: reasoning explanations for informed voting)
        triad_recommendations: dict[str, str] = {}
        triad_deliberations: dict[str, str] = {}
        if self.squad_id and self.identity.role != AgentRole.TRIAD_MEMBER:
            # Residents read Triad recommendations and deliberations for their squad
            import json

            # Phase 4: Recommendations
            recs_file = Path("data/.triad_recommendations.json")
            if recs_file.exists():
                try:
                    recs_data = json.loads(recs_file.read_text())
                    recommendations = recs_data.get("recommendations", {})
                    # Build per-proposal recommendations for our squad
                    for proposal_id, squad_recs in recommendations.items():
                        if self.squad_id in squad_recs:
                            triad_recommendations[proposal_id] = squad_recs[self.squad_id]
                    if triad_recommendations:
                        logger.debug("Agent %s received %d Triad recommendations", self.id, len(triad_recommendations))
                except Exception as e:
                    logger.debug("Agent %s failed to read Triad recommendations: %s", self.id, e)

            # Phase 5: Deliberations (reasoning from Triad)
            delib_file = Path("data/.squad_deliberations.json")
            if delib_file.exists():
                try:
                    delib_data = json.loads(delib_file.read_text())
                    deliberations = delib_data.get("deliberations", {})
                    # Build per-proposal deliberations for our squad
                    for proposal_id, squad_delibs in deliberations.items():
                        if self.squad_id in squad_delibs:
                            triad_deliberations[proposal_id] = squad_delibs[self.squad_id]
                    if triad_deliberations:
                        logger.debug("Agent %s received %d Triad deliberations", self.id, len(triad_deliberations))
                except Exception as e:
                    logger.debug("Agent %s failed to read Triad deliberations: %s", self.id, e)

        return VotingContext(
            recent_events=recent_events,
            milestones=milestones,
            personal_memory=personal_memory,
            voting_history=voting_history,
            squad_id=self.squad_id,
            squad_momentum=squad_momentum,
            triad_recommendations=triad_recommendations,
            triad_deliberations=triad_deliberations,
        )

    def _record_vote_outcome(
        self,
        proposal_id: str,
        action: ProposalAction,
        vote: bool,
        outcome: ProposalStatus,
        round_number: int,
    ) -> None:
        """Record a vote and its outcome for historical context."""
        record = VoteRecord(
            proposal_id=proposal_id,
            action=action,
            vote=vote,
            outcome=outcome,
            round_number=round_number,
        )
        self._voting_history.append(record)
        # Keep only recent history to prevent memory bloat
        if len(self._voting_history) > 100:
            self._voting_history = self._voting_history[-100:]
