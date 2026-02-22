"""Squad Competition System - Gamified inter-squad rivalry for consolidation.

Tracks squad performance, determines winners, and distributes rewards.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timezone

from .models import ProposalAction

logger = logging.getLogger("pureswarm.squad_competition")


@dataclass
class SquadScore:
    """Track a squad's performance metrics."""
    squad_id: str
    fuse_proposals: int = 0
    delete_proposals: int = 0
    fuse_adopted: int = 0
    delete_adopted: int = 0
    tenets_pruned: int = 0  # Total tenets removed/consolidated
    round_wins: int = 0

    @property
    def total_score(self) -> int:
        """Calculate total score: FUSE=3pts, DELETE=2pts per adoption, +bonus for volume."""
        return (self.fuse_adopted * 3) + (self.delete_adopted * 2) + (self.tenets_pruned // 5)

    @property
    def efficiency(self) -> float:
        """Adoption rate: adopted / proposed."""
        total_proposed = self.fuse_proposals + self.delete_proposals
        total_adopted = self.fuse_adopted + self.delete_adopted
        if total_proposed == 0:
            return 0.0
        return total_adopted / total_proposed


@dataclass
class RoundResult:
    """Result of a single round's competition."""
    round_number: int
    winner: Optional[str]
    scores: Dict[str, int]
    margin: int  # Winning margin
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SquadCompetition:
    """Gamified competition system for squad-based consolidation.

    Features:
    - Track FUSE/DELETE proposals and adoptions per squad
    - Determine round winners
    - Distribute rewards (dopamine + fitness)
    - Maintain leaderboard history
    """

    SQUADS = ["Alpha", "Beta", "Gamma"]

    # Reward multipliers
    WINNER_DOPAMINE_MULTIPLIER = 1.5
    WINNER_FITNESS_BONUS = 0.15
    RUNNERUP_FITNESS_BONUS = 0.05

    def __init__(self) -> None:
        self._scores: Dict[str, SquadScore] = {
            squad: SquadScore(squad_id=squad) for squad in self.SQUADS
        }
        self._round_history: List[RoundResult] = []
        self._current_round_proposals: Dict[str, List[str]] = {
            squad: [] for squad in self.SQUADS
        }
        self._current_round_adoptions: Dict[str, List[str]] = {
            squad: [] for squad in self.SQUADS
        }

    def record_proposal(self, squad_id: str, proposal_id: str, action: ProposalAction) -> None:
        """Record a consolidation proposal from a squad."""
        if squad_id not in self.SQUADS:
            return

        score = self._scores[squad_id]
        if action == ProposalAction.FUSE:
            score.fuse_proposals += 1
        elif action == ProposalAction.DELETE:
            score.delete_proposals += 1

        self._current_round_proposals[squad_id].append(proposal_id)
        logger.debug("Squad %s proposed %s [%s]", squad_id, action.value, proposal_id[:8])

    def record_adoption(self, squad_id: str, proposal_id: str, action: ProposalAction,
                       tenets_affected: int = 1) -> None:
        """Record an adopted consolidation proposal."""
        if squad_id not in self.SQUADS:
            return

        score = self._scores[squad_id]
        if action == ProposalAction.FUSE:
            score.fuse_adopted += 1
        elif action == ProposalAction.DELETE:
            score.delete_adopted += 1

        score.tenets_pruned += tenets_affected
        self._current_round_adoptions[squad_id].append(proposal_id)

        logger.info("SQUAD %s: +%d consolidation points! [%s affected %d tenets]",
                   squad_id, 3 if action == ProposalAction.FUSE else 2,
                   action.value, tenets_affected)

    def end_round(self, round_number: int) -> RoundResult:
        """Finalize round, determine winner, return results."""
        # Calculate round scores
        round_scores = {}
        for squad_id, adoptions in self._current_round_adoptions.items():
            # Points this round: count FUSE/DELETE adoptions
            fuse_count = sum(1 for pid in adoptions if self._is_fuse(pid))
            delete_count = len(adoptions) - fuse_count
            round_scores[squad_id] = (fuse_count * 3) + (delete_count * 2)

        # Determine winner
        sorted_squads = sorted(round_scores.items(), key=lambda x: x[1], reverse=True)
        winner = None
        margin = 0

        if sorted_squads[0][1] > 0:  # Must have at least one point to win
            if len(sorted_squads) > 1 and sorted_squads[0][1] > sorted_squads[1][1]:
                winner = sorted_squads[0][0]
                margin = sorted_squads[0][1] - sorted_squads[1][1]
                self._scores[winner].round_wins += 1
                logger.info("ROUND %d WINNER: Squad %s (+%d margin)!",
                           round_number, winner, margin)
            elif sorted_squads[0][1] == sorted_squads[1][1]:
                # Tie - no winner this round
                logger.info("ROUND %d: TIE between squads! No winner declared.", round_number)

        result = RoundResult(
            round_number=round_number,
            winner=winner,
            scores=round_scores,
            margin=margin
        )
        self._round_history.append(result)

        # Reset round tracking
        self._current_round_proposals = {squad: [] for squad in self.SQUADS}
        self._current_round_adoptions = {squad: [] for squad in self.SQUADS}

        return result

    def _is_fuse(self, proposal_id: str) -> bool:
        """Check if a proposal was a FUSE (heuristic based on ID or metadata)."""
        # In practice, we'd track this. For now, assume 50/50 if unknown.
        return hash(proposal_id) % 2 == 0

    def get_leaderboard(self) -> List[Dict]:
        """Get current leaderboard sorted by total score."""
        return sorted([
            {
                "squad": score.squad_id,
                "total_score": score.total_score,
                "fuse_adopted": score.fuse_adopted,
                "delete_adopted": score.delete_adopted,
                "tenets_pruned": score.tenets_pruned,
                "round_wins": score.round_wins,
                "efficiency": f"{score.efficiency:.1%}"
            }
            for score in self._scores.values()
        ], key=lambda x: x["total_score"], reverse=True)

    def get_squad_members_for_rewards(self, winner: str, agents: list) -> tuple[list, list]:
        """Get agent IDs for winner and runner-up squads for reward distribution.

        Returns:
            (winner_agent_ids, runnerup_agent_ids)
        """
        winner_ids = []
        runnerup_ids = []

        # Get runner-up (second place)
        leaderboard = self.get_leaderboard()
        runnerup = leaderboard[1]["squad"] if len(leaderboard) > 1 else None

        for agent in agents:
            if hasattr(agent, 'squad_id'):
                if agent.squad_id == winner:
                    winner_ids.append(agent.id)
                elif runnerup and agent.squad_id == runnerup:
                    runnerup_ids.append(agent.id)

        return winner_ids, runnerup_ids

    def get_stats_for_dashboard(self) -> Dict:
        """Get formatted stats for dashboard display."""
        leaderboard = self.get_leaderboard()

        return {
            "leaderboard": leaderboard,
            "total_rounds": len(self._round_history),
            "current_leader": leaderboard[0]["squad"] if leaderboard else None,
            "round_history": [
                {"round": r.round_number, "winner": r.winner, "margin": r.margin}
                for r in self._round_history[-5:]  # Last 5 rounds
            ]
        }
