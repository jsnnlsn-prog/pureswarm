"""Abstract base for agent reasoning strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Proposal, Tenet, AgentRole


class BaseStrategy(ABC):
    """Interface that all reasoning strategies must implement."""

    @abstractmethod
    def generate_proposal(
        self,
        agent_id: str,
        round_number: int,
        existing_tenets: list[Tenet],
        seed_prompt: str,
        role: AgentRole = AgentRole.RESIDENT,
        prophecy: str | None = None,
    ) -> str | None:
        """Return proposed tenet text, or None to skip this round."""

    @abstractmethod
    def evaluate_proposal(
        self,
        agent_id: str,
        proposal: Proposal,
        existing_tenets: list[Tenet],
        seed_prompt: str,
        role: AgentRole = AgentRole.RESIDENT,
        prophecy: str | None = None,
    ) -> bool:
        """Return True to vote YES, False to vote NO."""
