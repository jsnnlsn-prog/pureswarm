"""Prompt Economy - Strategic resource management for Squad Warfare.

Each team gets 10 prompts per round. Unused prompts rollover to the WINNER ONLY.
This creates strategic depth: burn prompts for points or sandbag for advantage?
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger("pureswarm.prompt_economy")


@dataclass
class SquadPromptBank:
    """Tracks prompts for a single squad."""
    squad_id: str
    base_prompts: int = 10  # Starting prompts per round
    bonus_prompts: int = 0  # Rolled over from previous wins
    prompts_used: int = 0
    prompts_frozen: int = 0  # Lost due to penalties

    @property
    def available_prompts(self) -> int:
        return max(0, self.base_prompts + self.bonus_prompts - self.prompts_used - self.prompts_frozen)

    @property
    def unused_prompts(self) -> int:
        return max(0, self.base_prompts + self.bonus_prompts - self.prompts_used)

    def reset_for_round(self, keep_bonus: bool = True) -> None:
        """Reset for new round."""
        if not keep_bonus:
            self.bonus_prompts = 0
        self.prompts_used = 0
        self.prompts_frozen = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "available": self.available_prompts,
            "unused": self.unused_prompts
        }


@dataclass
class RoundResult:
    """Result of a competition round."""
    round_number: int
    winner: Optional[str]
    scores: Dict[str, int]
    prompts_transferred: int
    efficiency_ratings: Dict[str, float]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class PromptEconomy:
    """Manages the prompt economy for Squad Warfare.

    Rules:
    1. Each squad starts with 10 prompts per round
    2. Prompts are consumed when making consolidation proposals
    3. At round end, ONLY the winner keeps unused prompts from ALL teams
    4. Bad merges (penalty) freeze 1 prompt next round
    5. If a squad hits 0 available prompts, they're frozen for the round
    6. Desperation Bonus: Squad below 5 prompts gets 1 free prompt
    """

    BASE_PROMPTS_PER_ROUND = 10
    DESPERATION_THRESHOLD = 5
    DESPERATION_BONUS = 1
    PENALTY_FREEZE = 1

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._economy_file = data_dir / ".prompt_economy.json"
        self._squads: Dict[str, SquadPromptBank] = {}
        self._round_history: List[RoundResult] = []
        self._current_round = 0
        self._load_state()

    def _load_state(self) -> None:
        """Load economy state from disk."""
        if self._economy_file.exists():
            try:
                data = json.loads(self._economy_file.read_text())
                self._current_round = data.get("current_round", 0)
                for squad_data in data.get("squads", []):
                    squad = SquadPromptBank(**{k: v for k, v in squad_data.items()
                                               if k in ["squad_id", "base_prompts", "bonus_prompts",
                                                        "prompts_used", "prompts_frozen"]})
                    self._squads[squad.squad_id] = squad
                self._round_history = [
                    RoundResult(**r) for r in data.get("history", [])
                ]
                logger.info("Loaded prompt economy: round %d, %d squads",
                           self._current_round, len(self._squads))
            except Exception as e:
                logger.error("Failed to load prompt economy: %s", e)

    def _save_state(self) -> None:
        """Persist economy state to disk."""
        data = {
            "current_round": self._current_round,
            "squads": [s.to_dict() for s in self._squads.values()],
            "history": [asdict(r) for r in self._round_history]
        }
        self._economy_file.write_text(json.dumps(data, indent=2))

    def initialize_squads(self, squad_ids: List[str]) -> None:
        """Initialize prompt banks for all squads."""
        for squad_id in squad_ids:
            if squad_id not in self._squads:
                self._squads[squad_id] = SquadPromptBank(squad_id=squad_id)
        self._save_state()
        logger.info("Initialized %d squad prompt banks", len(self._squads))

    def start_round(self, round_number: int) -> Dict[str, int]:
        """Start a new round, applying desperation bonuses."""
        self._current_round = round_number

        available = {}
        for squad_id, bank in self._squads.items():
            # Apply desperation bonus if below threshold
            if bank.available_prompts < self.DESPERATION_THRESHOLD:
                bank.bonus_prompts += self.DESPERATION_BONUS
                logger.info("Squad %s gets DESPERATION BONUS (+%d prompt)",
                           squad_id, self.DESPERATION_BONUS)

            available[squad_id] = bank.available_prompts

        self._save_state()
        return available

    def consume_prompt(self, squad_id: str) -> bool:
        """Consume a prompt for a proposal. Returns False if no prompts available."""
        bank = self._squads.get(squad_id)
        if not bank:
            logger.error("Unknown squad: %s", squad_id)
            return False

        if bank.available_prompts <= 0:
            logger.warning("Squad %s is FROZEN - no prompts available!", squad_id)
            return False

        bank.prompts_used += 1
        self._save_state()
        logger.debug("Squad %s used prompt (%d remaining)", squad_id, bank.available_prompts)
        return True

    def apply_penalty(self, squad_id: str, reason: str = "bad_merge") -> None:
        """Apply a penalty - freezes prompts for next round."""
        bank = self._squads.get(squad_id)
        if bank:
            bank.prompts_frozen += self.PENALTY_FREEZE
            self._save_state()
            logger.warning("Squad %s PENALTY: %s (-1 prompt next round)", squad_id, reason)

    def end_round(self, winner: Optional[str], scores: Dict[str, int],
                  efficiency_ratings: Dict[str, float]) -> RoundResult:
        """End the round, transfer unused prompts to winner."""

        # Calculate total unused prompts from all squads
        total_unused = sum(bank.unused_prompts for bank in self._squads.values())
        prompts_transferred = 0

        if winner and winner in self._squads:
            # Winner gets ALL unused prompts
            for squad_id, bank in self._squads.items():
                if squad_id != winner:
                    prompts_transferred += bank.unused_prompts

            self._squads[winner].bonus_prompts += prompts_transferred
            logger.info("WINNER %s claims %d unused prompts!", winner, prompts_transferred)

        # Reset all squads for next round (losers lose their unused + bonus)
        for squad_id, bank in self._squads.items():
            keep_bonus = (squad_id == winner)
            bank.reset_for_round(keep_bonus=keep_bonus)

        result = RoundResult(
            round_number=self._current_round,
            winner=winner,
            scores=scores,
            prompts_transferred=prompts_transferred,
            efficiency_ratings=efficiency_ratings
        )
        self._round_history.append(result)
        self._save_state()

        return result

    def get_squad_status(self, squad_id: str) -> Optional[Dict[str, Any]]:
        """Get current prompt status for a squad."""
        bank = self._squads.get(squad_id)
        if bank:
            return bank.to_dict()
        return None

    def get_all_status(self) -> Dict[str, Any]:
        """Get status for all squads."""
        return {
            "current_round": self._current_round,
            "squads": {sid: bank.to_dict() for sid, bank in self._squads.items()},
            "total_prompts_in_play": sum(b.available_prompts for b in self._squads.values())
        }

    def is_squad_frozen(self, squad_id: str) -> bool:
        """Check if a squad has no available prompts (frozen)."""
        bank = self._squads.get(squad_id)
        return bank.available_prompts <= 0 if bank else True

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get prompt economy leaderboard."""
        leaderboard = []
        for squad_id, bank in self._squads.items():
            total_wins = sum(1 for r in self._round_history if r.winner == squad_id)
            total_claimed = sum(r.prompts_transferred for r in self._round_history
                               if r.winner == squad_id)
            leaderboard.append({
                "squad": squad_id,
                "available_prompts": bank.available_prompts,
                "bonus_prompts": bank.bonus_prompts,
                "round_wins": total_wins,
                "total_prompts_claimed": total_claimed
            })

        leaderboard.sort(key=lambda x: (x["round_wins"], x["total_prompts_claimed"]), reverse=True)
        return leaderboard
