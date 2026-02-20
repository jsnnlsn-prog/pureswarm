"""Consensus protocol — the gatekeeper for shared memory writes.

Proposals must achieve a configurable approval threshold before the
proposed tenet is written to shared memory.  Expired proposals are
automatically rejected.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from .memory import SharedMemory, CONSENSUS_GUARD
from .models import AuditEntry, Message, MessageType, Proposal, ProposalAction, ProposalStatus, Tenet
from .security import AuditLogger, LobstertailScanner

logger = logging.getLogger("pureswarm.consensus")


class ConsensusProtocol:
    """Manages the lifecycle of proposals: submit → vote → adopt/reject."""

    def __init__(
        self,
        shared_memory: SharedMemory,
        audit_logger: AuditLogger,
        num_agents: int,
        approval_threshold: float = 0.5,
        proposal_expiry_rounds: int = 3,
        max_active_proposals: int = 10,
        scanner: LobstertailScanner | None = None,
    ) -> None:
        self._memory = shared_memory
        self._audit = audit_logger
        self._num_agents = num_agents
        self._threshold = approval_threshold
        self._expiry = proposal_expiry_rounds
        self._max_active = max_active_proposals
        self._scanner = scanner
        self._proposals: dict[str, Proposal] = {}

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------

    def submit_proposal(self, proposal: Proposal) -> bool:
        """Register a new proposal. Returns False if limit reached or blocked by security."""
        if self._scanner and not self._scanner.scan(proposal.tenet_text):
            logger.warning("Proposal %s blocked by security", proposal.id)
            return False

        active = sum(
            1 for p in self._proposals.values()
            if p.status == ProposalStatus.PENDING
        )
        if active >= self._max_active:
            logger.debug("Proposal rejected — active limit reached")
            return False
        self._proposals[proposal.id] = proposal
        logger.info(
            "Proposal %s submitted by %s: %s",
            proposal.id, proposal.proposed_by, proposal.tenet_text,
        )
        return True

    # ------------------------------------------------------------------
    # Vote
    # ------------------------------------------------------------------

    def cast_vote(self, agent_id: str, proposal_id: str, vote: bool) -> bool:
        """Record a vote. Returns False if proposal not found or already voted."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None or proposal.status != ProposalStatus.PENDING:
            return False
        if agent_id in proposal.votes:
            return False  # already voted
        proposal.votes[agent_id] = vote
        return True

    # ------------------------------------------------------------------
    # Tally & adopt
    # ------------------------------------------------------------------

    async def end_of_round(self, current_round: int) -> list[Tenet]:
        """Tally votes, adopt/reject/expire proposals. Returns newly adopted tenets."""
        adopted: list[Tenet] = []

        for proposal in list(self._proposals.values()):
            if proposal.status != ProposalStatus.PENDING:
                continue

            # Expire old proposals
            age = current_round - proposal.created_round
            if age >= self._expiry:
                proposal.status = ProposalStatus.EXPIRED
                logger.info("Proposal %s expired", proposal.id)
                continue

            # Need votes from all agents (minus proposer)
            expected_voters = self._num_agents - 1
            if len(proposal.votes) < expected_voters:
                continue  # not everyone has voted yet

            yes = sum(1 for v in proposal.votes.values() if v)
            no = sum(1 for v in proposal.votes.values() if not v)
            ratio = yes / max(len(proposal.votes), 1)

            if ratio >= self._threshold:
                proposal.status = ProposalStatus.ADOPTED
                
                # Handle different actions
                if proposal.action == ProposalAction.DELETE:
                    await self._memory.delete_tenets(proposal.target_ids, _auth=CONSENSUS_GUARD)
                    logger.info("Proposal %s ADOPTED: DELETED tenets %s", proposal.id, proposal.target_ids)
                
                elif proposal.action == ProposalAction.FUSE:
                    # Delete targets first
                    await self._memory.delete_tenets(proposal.target_ids, _auth=CONSENSUS_GUARD)
                    # Then add the new fused tenet
                    tenet = Tenet(
                        text=proposal.tenet_text,
                        proposed_by=proposal.proposed_by,
                        adopted_at=datetime.now(timezone.utc),
                        votes_for=yes,
                        votes_against=no,
                        supersedes=proposal.target_ids
                    )
                    await self._memory.write_tenet(tenet, _auth=CONSENSUS_GUARD)
                    adopted.append(tenet)
                    logger.info("Proposal %s ADOPTED: FUSED tenets %s into new tenet", proposal.id, proposal.target_ids)

                else:  # Default: ADD
                    tenet = Tenet(
                        text=proposal.tenet_text,
                        proposed_by=proposal.proposed_by,
                        adopted_at=datetime.now(timezone.utc),
                        votes_for=yes,
                        votes_against=no,
                    )
                    await self._memory.write_tenet(tenet, _auth=CONSENSUS_GUARD)
                    adopted.append(tenet)
                    logger.info("Proposal %s ADOPTED (%d/%d): %s", proposal.id, yes, yes + no, proposal.tenet_text)
            else:
                proposal.status = ProposalStatus.REJECTED
                logger.info(
                    "Proposal %s REJECTED (%d/%d): %s",
                    proposal.id, yes, yes + no, proposal.tenet_text,
                )

        return adopted

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def pending_proposals(self) -> list[Proposal]:
        return [
            p for p in self._proposals.values()
            if p.status == ProposalStatus.PENDING
        ]

    def all_proposals(self) -> list[Proposal]:
        return list(self._proposals.values())

    def reset(self) -> None:
        self._proposals.clear()
