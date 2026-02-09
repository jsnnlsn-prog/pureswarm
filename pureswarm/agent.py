"""Agent runtime — the perceive-reason-act-reflect loop."""

from __future__ import annotations

import logging
from pathlib import Path

from .consensus import ConsensusProtocol
from .memory import SharedMemory
from .message_bus import MessageBus
from .models import (
    AgentIdentity,
    AuditEntry,
    Message,
    MessageType,
    Proposal,
    ProposalStatus,
)
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
    ) -> None:
        self.identity = identity
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

        # Identity Fusion & Internet Tools (only for Triad)
        from .models import AgentRole
        from .tools.internet import InternetAccess
        is_triad = self.identity.role == AgentRole.TRIAD_MEMBER
        self._internet = InternetAccess(self.id, is_triad)

        # Internal state
        self._round_observations: list[str] = []
        self._lifetime_memory: list[str] = []

    @property
    def id(self) -> str:
        return self.identity.id

    @property
    def name(self) -> str:
        return self.identity.name

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
                     # 1. External Action / Fusion
                     if "EXTERNAL:" in prophecy.content:
                         task = prophecy.content.split("EXTERNAL:")[1].strip()
                         self._internet.perform_fusion_task(task)
                     
                     # 2. Market Research
                     if "RESEARCH:" in prophecy.content:
                         query = prophecy.content.split("RESEARCH:")[1].strip()
                         insight = self._internet.search_market(query)
                         self._lifetime_memory.append(f"Divine Insight: {insight}")

        # 1. PERCEIVE
        messages = await self._bus.receive(self.id)
        tenets = await self._memory.read_tenets()
        await self._perceive(messages)
        stats = {"proposals_made": 0, "votes_cast": 0}

        # 2. REASON & ACT — vote on pending proposals
        pending = self._consensus.pending_proposals()
        votes_this_round = 0
        
        # Get latest prophecy text for strategy
        prophecy_text = None
        if self._prophecy_engine:
            p = self._prophecy_engine.get_latest_prophecy()
            if p:
                prophecy_text = p.content

        for proposal in pending:
            if proposal.proposed_by == self.id:
                continue  # don't vote on own proposals
            if self.id in proposal.votes:
                continue  # already voted
            if votes_this_round >= self._max_votes:
                break

            vote = self._strategy.evaluate_proposal(
                self.id, proposal, tenets, self._seed_prompt,
                role=self.identity.role,
                prophecy=prophecy_text
            )
            accepted = self._consensus.cast_vote(self.id, proposal.id, vote)
            if accepted:
                votes_this_round += 1
                stats["votes_cast"] += 1

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
                        },
                    )
                )

        # 3. ACT — maybe propose a new tenet
        proposals_made = 0
        if proposals_made < self._max_proposals:
            text = self._strategy.generate_proposal(
                self.id, round_number, tenets, self._seed_prompt,
                role=self.identity.role,
                prophecy=prophecy_text
            )
            if text is not None:
                # Security self-check
                if self._scanner and not self._scanner.scan(text):
                    logger.warning("Agent %s suppressed malicious proposal locally", self.id)
                    self._lifetime_memory.append(f"Round {round_number}: Proposal blocked by security intent.")
                else:
                    proposal = Proposal(
                        tenet_text=text,
                        proposed_by=self.id,
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
