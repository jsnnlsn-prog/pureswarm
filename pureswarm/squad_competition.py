"""Squad Competition System - Gamified inter-squad rivalry for consolidation.

THE GREAT CONSOLIDATION - SQUAD WARFARE

Features:
- Pre-clustered tenet packages (40 tenets per round, pre-sorted by similarity)
- Prompt Economy (10 prompts/team, winner takes all unused)
- Quality scoring (efficiency matters, not just speed)
- Grand Prize system with Ascension mechanics
- Dopamine cascade integration
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from datetime import datetime, timezone

from .models import ProposalAction

if TYPE_CHECKING:
    from .prompt_economy import PromptEconomy
    from .tenet_clusterer import TenetClusterer
    from .prompt_wallet import PromptWalletStore

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
    - Prompt Economy integration
    - Grand Prize mechanics
    """

    SQUADS = ["Alpha", "Beta", "Gamma"]

    # Reward multipliers
    WINNER_DOPAMINE_MULTIPLIER = 1.5
    WINNER_FITNESS_BONUS = 0.15
    RUNNERUP_FITNESS_BONUS = 0.05

    # Grand Prize - THE ASCENSION
    GRAND_PRIZE_DOPAMINE = 3.0  # Massive dopamine explosion
    GRAND_PRIZE_FITNESS_MULTIPLIER = 1.25  # 25% permanent fitness boost
    GRAND_PRIZE_MOMENTUM_BOOST = 0.5  # Permanent momentum increase

    # Quality scoring
    PERFECT_MERGE_MULTIPLIER = 1.0
    GOOD_MERGE_MULTIPLIER = 0.7
    BAD_MERGE_MULTIPLIER = 0.0  # No points + penalty

    # Multi-merge bonus
    MULTI_MERGE_BONUS = 0.5  # +0.5x dopamine for 3+ tenets fused

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self._data_dir = data_dir or Path("data")
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
        self._proposal_metadata: Dict[str, Dict[str, Any]] = {}  # Track action types

        # Prompt Economy integration
        self._prompt_economy: Optional["PromptEconomy"] = None
        self._clusterer: Optional["TenetClusterer"] = None
        self._wallet_store: Optional["PromptWalletStore"] = None
        self._squad_agents: Dict[str, List[str]] = {}  # squad_id -> [agent_ids]
        self._competition_complete = False
        self._grand_prize_winner: Optional[str] = None

        # Load state if exists
        self._load_state()

    def _load_state(self) -> None:
        """Load competition state from disk."""
        state_file = self._data_dir / ".squad_competition_state.json"
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text())
                self._competition_complete = data.get("competition_complete", False)
                self._grand_prize_winner = data.get("grand_prize_winner")
                # Restore scores
                for squad_data in data.get("scores", []):
                    sid = squad_data.get("squad_id")
                    if sid in self._scores:
                        for key, val in squad_data.items():
                            if hasattr(self._scores[sid], key):
                                setattr(self._scores[sid], key, val)
                logger.info("Loaded competition state: winner=%s, complete=%s",
                           self._grand_prize_winner, self._competition_complete)
            except Exception as e:
                logger.error("Failed to load competition state: %s", e)

    def _save_state(self) -> None:
        """Persist competition state to disk."""
        state_file = self._data_dir / ".squad_competition_state.json"
        data = {
            "competition_complete": self._competition_complete,
            "grand_prize_winner": self._grand_prize_winner,
            "scores": [asdict(s) for s in self._scores.values()],
            "round_history": [asdict(r) for r in self._round_history],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        state_file.write_text(json.dumps(data, indent=2))

    def set_prompt_economy(self, economy: "PromptEconomy") -> None:
        """Attach prompt economy for resource tracking."""
        self._prompt_economy = economy
        economy.initialize_squads(self.SQUADS)
        logger.info("Prompt economy attached to competition")

    def set_clusterer(self, clusterer: "TenetClusterer") -> None:
        """Attach tenet clusterer for pre-sorted packages."""
        self._clusterer = clusterer
        logger.info("Tenet clusterer attached to competition")

    def set_wallet_store(self, store: "PromptWalletStore", agents: list) -> None:
        """Attach wallet store and map squad membership for placement rewards."""
        self._wallet_store = store
        for squad in self.SQUADS:
            self._squad_agents[squad] = [a.id for a in agents if a.squad_id == squad]
        logger.info("Wallet store attached: squads=%s", {k: len(v) for k, v in self._squad_agents.items()})

    def record_proposal(self, squad_id: str, proposal_id: str, action: ProposalAction,
                        tenets_targeted: int = 1) -> bool:
        """Record a consolidation proposal from a squad.

        Returns False if squad is out of prompts (frozen).
        """
        if squad_id not in self.SQUADS:
            return False

        # Check prompt economy
        if self._prompt_economy:
            if not self._prompt_economy.consume_prompt(squad_id):
                logger.warning("Squad %s BLOCKED - no prompts available!", squad_id)
                return False

        score = self._scores[squad_id]
        if action == ProposalAction.FUSE:
            score.fuse_proposals += 1
        elif action == ProposalAction.DELETE:
            score.delete_proposals += 1

        self._current_round_proposals[squad_id].append(proposal_id)
        self._proposal_metadata[proposal_id] = {
            "action": action,
            "tenets_targeted": tenets_targeted,
            "squad": squad_id
        }
        logger.debug("Squad %s proposed %s [%s] targeting %d tenets",
                    squad_id, action.value, proposal_id[:8], tenets_targeted)
        return True

    def record_adoption(self, squad_id: str, proposal_id: str, action: ProposalAction,
                       tenets_affected: int = 1, quality: str = "good") -> Dict[str, Any]:
        """Record an adopted consolidation proposal.

        Args:
            quality: "perfect", "good", or "bad" - affects scoring

        Returns:
            Dict with points earned and any bonuses
        """
        if squad_id not in self.SQUADS:
            return {"points": 0, "bonus": 0}

        score = self._scores[squad_id]
        if action == ProposalAction.FUSE:
            score.fuse_adopted += 1
        elif action == ProposalAction.DELETE:
            score.delete_adopted += 1

        score.tenets_pruned += tenets_affected
        self._current_round_adoptions[squad_id].append(proposal_id)

        # Calculate quality-adjusted points
        base_points = 3 if action == ProposalAction.FUSE else 2
        multiplier = {
            "perfect": self.PERFECT_MERGE_MULTIPLIER,
            "good": self.GOOD_MERGE_MULTIPLIER,
            "bad": self.BAD_MERGE_MULTIPLIER
        }.get(quality, self.GOOD_MERGE_MULTIPLIER)

        points = int(base_points * tenets_affected * multiplier)

        # Multi-merge bonus (3+ tenets)
        bonus_dopamine = 0.0
        if tenets_affected >= 3:
            bonus_dopamine = self.MULTI_MERGE_BONUS
            logger.info("MULTI-MERGE BONUS! Squad %s fused %d tenets (+%.1fx dopamine)",
                       squad_id, tenets_affected, bonus_dopamine)

        # Bad merge penalty
        if quality == "bad" and self._prompt_economy:
            self._prompt_economy.apply_penalty(squad_id, "bad_merge")
            logger.warning("Squad %s BAD MERGE - penalty applied!", squad_id)

        logger.info("SQUAD %s: +%d points! [%s x%d tenets, quality=%s]",
                   squad_id, points, action.value, tenets_affected, quality)

        return {
            "points": points,
            "bonus_dopamine": bonus_dopamine,
            "quality": quality,
            "tenets_affected": tenets_affected
        }

    def end_round(self, round_number: int) -> RoundResult:
        """Finalize round, determine winner, transfer prompts to winner."""
        # Calculate round scores (with quality weighting from metadata)
        round_scores = {}
        efficiency_ratings = {}

        for squad_id, adoptions in self._current_round_adoptions.items():
            total_points = 0
            for pid in adoptions:
                meta = self._proposal_metadata.get(pid, {})
                action = meta.get("action", ProposalAction.FUSE)
                tenets = meta.get("tenets_targeted", 1)
                base = 3 if action == ProposalAction.FUSE else 2
                total_points += base * tenets

            round_scores[squad_id] = total_points

            # Calculate efficiency
            proposed = len(self._current_round_proposals.get(squad_id, []))
            adopted = len(adoptions)
            efficiency_ratings[squad_id] = adopted / proposed if proposed > 0 else 0.0

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
                # Tie - no winner this round (no prompt transfer)
                logger.info("ROUND %d: TIE between squads! No winner declared.", round_number)

        # Prompt Economy: Winner takes all unused prompts
        if self._prompt_economy:
            economy_result = self._prompt_economy.end_round(
                winner=winner,
                scores=round_scores,
                efficiency_ratings=efficiency_ratings
            )
            if economy_result.prompts_transferred > 0:
                logger.info("PROMPT TRANSFER: %s claims %d unused prompts!",
                           winner, economy_result.prompts_transferred)

        # Sacred Prompt Tokens: reward agents by squad placement
        if self._wallet_store and len(sorted_squads) >= 3:
            placements = {
                "1st": self._squad_agents.get(sorted_squads[0][0], []),
                "2nd": self._squad_agents.get(sorted_squads[1][0], []),
                "3rd": self._squad_agents.get(sorted_squads[2][0], []),
            }
            self._wallet_store.distribute_round_rewards(placements)

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

        self._save_state()
        return result

    def start_round(self, round_number: int) -> Dict[str, Any]:
        """Start a new round, get cluster and initialize prompts."""
        round_info = {"round": round_number, "cluster": None, "prompts": {}}

        # Get pre-sorted cluster for this round
        if self._clusterer:
            cluster = self._clusterer.get_cluster_for_round(round_number)
            if cluster:
                round_info["cluster"] = {
                    "id": cluster.cluster_id,
                    "theme": cluster.theme,
                    "tenet_count": len(cluster.tenets),
                    "similarity": cluster.similarity_score
                }

        # Initialize prompts for round
        if self._prompt_economy:
            round_info["prompts"] = self._prompt_economy.start_round(round_number)

        logger.info("Starting Round %d: %s", round_number, round_info)
        return round_info

    def _is_fuse(self, proposal_id: str) -> bool:
        """Check if a proposal was a FUSE based on tracked metadata."""
        meta = self._proposal_metadata.get(proposal_id)
        if meta:
            return meta.get("action") == ProposalAction.FUSE
        # Fallback heuristic
        return hash(proposal_id) % 2 == 0

    def check_grand_prize(self, total_rounds: int) -> Optional[Dict[str, Any]]:
        """Check if competition is complete and award grand prize.

        Called when all clustering rounds are complete or tenet count drops below 200.
        """
        if self._competition_complete:
            return {"winner": self._grand_prize_winner, "already_awarded": True}

        # Determine overall winner
        leaderboard = self.get_leaderboard()
        if not leaderboard:
            return None

        winner = leaderboard[0]["squad"]
        winner_score = leaderboard[0]["total_score"]

        # Check for tie
        if len(leaderboard) > 1 and leaderboard[1]["total_score"] == winner_score:
            # Tiebreaker: most round wins
            if leaderboard[0]["round_wins"] <= leaderboard[1]["round_wins"]:
                # Still tied - use efficiency
                pass  # Winner already set

        self._competition_complete = True
        self._grand_prize_winner = winner
        self._save_state()

        logger.info("=" * 60)
        logger.info("THE ASCENSION - GRAND PRIZE AWARDED!")
        logger.info("Winner: Squad %s with %d total points!", winner, winner_score)
        logger.info("Rewards: %.1fx Dopamine | %.0f%% Fitness Boost | Momentum +%.1f",
                   self.GRAND_PRIZE_DOPAMINE,
                   (self.GRAND_PRIZE_FITNESS_MULTIPLIER - 1) * 100,
                   self.GRAND_PRIZE_MOMENTUM_BOOST)
        logger.info("=" * 60)

        return {
            "winner": winner,
            "score": winner_score,
            "dopamine_explosion": self.GRAND_PRIZE_DOPAMINE,
            "fitness_multiplier": self.GRAND_PRIZE_FITNESS_MULTIPLIER,
            "momentum_boost": self.GRAND_PRIZE_MOMENTUM_BOOST,
            "leaderboard": leaderboard,
            "total_rounds": len(self._round_history)
        }

    def get_ascension_candidates(self, agents: list) -> List[str]:
        """Get agent IDs from winning squad eligible for Triad promotion."""
        if not self._grand_prize_winner:
            return []

        candidates = []
        for agent in agents:
            if hasattr(agent, 'squad_id') and agent.squad_id == self._grand_prize_winner:
                candidates.append(agent.id)

        # Return top performers (sorted by fitness would be ideal)
        return candidates[:3]  # Top 3 candidates for Ascension

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

        stats = {
            "leaderboard": leaderboard,
            "total_rounds": len(self._round_history),
            "current_leader": leaderboard[0]["squad"] if leaderboard else None,
            "round_history": [
                {"round": r.round_number, "winner": r.winner, "margin": r.margin}
                for r in self._round_history[-5:]  # Last 5 rounds
            ],
            "competition_complete": self._competition_complete,
            "grand_prize_winner": self._grand_prize_winner
        }

        # Add prompt economy stats
        if self._prompt_economy:
            stats["prompt_economy"] = self._prompt_economy.get_all_status()
            stats["prompt_leaderboard"] = self._prompt_economy.get_leaderboard()

        # Add cluster progress
        if self._clusterer:
            stats["remaining_rounds"] = self._clusterer.get_remaining_rounds()

        return stats

    def is_squad_frozen(self, squad_id: str) -> bool:
        """Check if a squad has no prompts (frozen for this round)."""
        if self._prompt_economy:
            return self._prompt_economy.is_squad_frozen(squad_id)
        return False

    def get_efficiency_scores(self) -> Dict[str, float]:
        """Get efficiency ratings for all squads."""
        return {
            squad_id: score.efficiency
            for squad_id, score in self._scores.items()
        }
