"""Sacred Prompt Economy — per-agent wallets, rewards, gifting, trading, rate limiting.

Prompts are information tokens. They are scarce, transferable, and sacred.
Only Triad/Researchers can spend them on LLM calls.
Any agent can hold, give, or trade them.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("pureswarm.prompt_wallet")

# Reward amounts by placement
PLACEMENT_REWARDS = {
    "1st": 3,
    "2nd": 2,
    "3rd": 1,
}


@dataclass
class WalletTransaction:
    """A single token movement — the audit trail of the economy."""

    type: str               # "reward", "spend", "give", "receive", "trade"
    amount: int
    counterparty: Optional[str]  # agent_id or "system"
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "amount": self.amount,
            "counterparty": self.counterparty,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WalletTransaction":
        return cls(
            type=d["type"],
            amount=d["amount"],
            counterparty=d.get("counterparty"),
            reason=d.get("reason", ""),
            timestamp=d.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class AgentWallet:
    """An agent's sacred token holdings. Every token has a history."""

    agent_id: str
    balance: int = 0
    transactions: list = field(default_factory=list)  # list[WalletTransaction]

    def credit(self, amount: int, counterparty: Optional[str], reason: str) -> None:
        """Add tokens to this wallet."""
        if amount <= 0:
            return
        self.balance += amount
        self.transactions.append(WalletTransaction(
            type="receive" if counterparty and counterparty != "system" else "reward",
            amount=amount,
            counterparty=counterparty,
            reason=reason,
        ))
        logger.debug("Wallet %s: +%d (%s) → balance=%d", self.agent_id, amount, reason, self.balance)

    def debit(self, amount: int, counterparty: Optional[str], reason: str) -> bool:
        """Remove tokens. Returns False if insufficient balance."""
        if amount <= 0:
            return True
        if self.balance < amount:
            logger.debug("Wallet %s: insufficient balance (%d < %d)", self.agent_id, self.balance, amount)
            return False
        self.balance -= amount
        self.transactions.append(WalletTransaction(
            type="spend",
            amount=amount,
            counterparty=counterparty,
            reason=reason,
        ))
        logger.debug("Wallet %s: -%d (%s) → balance=%d", self.agent_id, amount, reason, self.balance)
        return True

    def transfer_to(self, other: "AgentWallet", amount: int, reason: str) -> bool:
        """True transfer — tokens leave this wallet and enter another. Sacred = scarce."""
        if amount <= 0 or self.balance < amount:
            return False
        self.balance -= amount
        self.transactions.append(WalletTransaction(
            type="give",
            amount=amount,
            counterparty=other.agent_id,
            reason=reason,
        ))
        other.balance += amount
        other.transactions.append(WalletTransaction(
            type="receive",
            amount=amount,
            counterparty=self.agent_id,
            reason=reason,
        ))
        logger.info("Wallet transfer: %s → %s  %d tokens (%s)", self.agent_id, other.agent_id, amount, reason)
        return True

    def to_dict(self) -> dict:
        return {
            "balance": self.balance,
            "transactions": [t.to_dict() for t in self.transactions[-100:]],  # keep last 100
        }

    @classmethod
    def from_dict(cls, agent_id: str, d: dict) -> "AgentWallet":
        wallet = cls(agent_id=agent_id, balance=d.get("balance", 0))
        wallet.transactions = [WalletTransaction.from_dict(t) for t in d.get("transactions", [])]
        return wallet


class PromptRateLimiter:
    """Hive-wide sliding window rate limiter. Default: 8 LLM calls per minute.

    Prevents API 429s by enforcing a ceiling across ALL agents.
    Configurable via PROMPT_RATE_LIMIT environment variable.
    """

    def __init__(self) -> None:
        max_env = os.getenv("PROMPT_RATE_LIMIT", "8")
        try:
            self.max_per_minute: int = int(max_env)
        except ValueError:
            self.max_per_minute = 8
        self._window: deque = deque()  # timestamps of recent spends
        self._lock = asyncio.Lock()
        logger.info("PromptRateLimiter initialized: %d calls/minute", self.max_per_minute)

    def can_spend(self) -> bool:
        """Check if a spend is allowed right now (non-blocking)."""
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - 60.0
        # Purge old entries
        while self._window and self._window[0] < cutoff:
            self._window.popleft()
        return len(self._window) < self.max_per_minute

    async def wait_for_slot(self) -> None:
        """Wait until a rate limit slot is available, then claim it."""
        async with self._lock:
            while True:
                now = datetime.now(timezone.utc).timestamp()
                cutoff = now - 60.0
                while self._window and self._window[0] < cutoff:
                    self._window.popleft()

                if len(self._window) < self.max_per_minute:
                    self._window.append(now)
                    return

                # Wait until the oldest entry expires
                wait_seconds = (self._window[0] + 60.0) - now + 0.1
                logger.debug("Rate limiter: %d/%d calls used, sleeping %.1fs",
                             len(self._window), self.max_per_minute, wait_seconds)
                await asyncio.sleep(wait_seconds)


class PromptWalletStore:
    """Persists all agent wallets and distributes round rewards.

    Backed by data/prompt_wallets.json.
    Lazy-creates wallets on first access.
    """

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._path = data_dir / "prompt_wallets.json"
        self._wallets: dict[str, AgentWallet] = {}
        self._load()

    # ------------------------------------------------------------------
    # Wallet access
    # ------------------------------------------------------------------

    def get_wallet(self, agent_id: str) -> AgentWallet:
        """Return wallet for agent, creating it if it doesn't exist."""
        if agent_id not in self._wallets:
            self._wallets[agent_id] = AgentWallet(agent_id=agent_id)
        return self._wallets[agent_id]

    # ------------------------------------------------------------------
    # Rewards
    # ------------------------------------------------------------------

    def distribute_round_rewards(self, placements: dict[str, list[str]]) -> None:
        """Award tokens to agents by their squad's placement this round.

        Args:
            placements: {"1st": [agent_ids], "2nd": [agent_ids], "3rd": [agent_ids]}
        """
        for place, agent_ids in placements.items():
            amount = PLACEMENT_REWARDS.get(place, 0)
            if amount == 0:
                continue
            for agent_id in agent_ids:
                wallet = self.get_wallet(agent_id)
                wallet.credit(amount, "system", f"Squad {place} place reward")
            logger.info("Round rewards: %s place → %d agents × %d tokens",
                        place, len(agent_ids), amount)
        self._save()

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_leaderboard(self, top_n: int = 10) -> list[tuple[str, int]]:
        """Return top agents by token balance."""
        ranked = sorted(self._wallets.items(), key=lambda x: x[1].balance, reverse=True)
        return [(agent_id, w.balance) for agent_id, w in ranked[:top_n]]

    def total_supply(self) -> int:
        """Total tokens in circulation across all wallets."""
        return sum(w.balance for w in self._wallets.values())

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self) -> None:
        try:
            data = {
                "wallets": {
                    agent_id: wallet.to_dict()
                    for agent_id, wallet in self._wallets.items()
                }
            }
            self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error("Failed to save prompt wallets: %s", e)

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            for agent_id, wallet_data in data.get("wallets", {}).items():
                self._wallets[agent_id] = AgentWallet.from_dict(agent_id, wallet_data)
            logger.info("Loaded prompt wallets: %d agents, %d total tokens",
                        len(self._wallets), self.total_supply())
        except Exception as e:
            logger.error("Failed to load prompt wallets: %s", e)

    def save(self) -> None:
        """Public save — call after manual wallet operations."""
        self._save()
