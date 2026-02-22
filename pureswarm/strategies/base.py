"""Abstract base for agent reasoning strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Proposal, Tenet, AgentRole, QueryResponse


class BaseStrategy(ABC):
    """Interface that all reasoning strategies must implement."""

    @abstractmethod
    async def generate_proposal(
        self,
        agent_id: str,
        round_number: int,
        existing_tenets: list[Tenet],
        seed_prompt: str,
        role: AgentRole = AgentRole.RESIDENT,
        prophecy: str | None = None,
        specialization: str | None = None,
    ) -> str | None:
        """Return proposed tenet text, or None to skip this round."""

    @abstractmethod
    async def evaluate_proposal(
        self,
        agent_id: str,
        proposal: Proposal,
        existing_tenets: list[Tenet],
        seed_prompt: str,
        role: AgentRole = AgentRole.RESIDENT,
        prophecy: str | None = None,
        squad_id: str | None = None,
        specialization: str | None = None,
    ) -> bool:
        """Return True to vote YES, False to vote NO.

        Args:
            agent_id: The voting agent's ID
            proposal: The proposal to evaluate
            existing_tenets: Current shared belief system
            seed_prompt: The hive's founding purpose
            role: Agent's role (RESIDENT, TRIAD_MEMBER, RESEARCHER)
            prophecy: Current prophecy from Sovereign (if any)
            squad_id: Agent's squad (Alpha, Beta, Gamma)
            specialization: Agent's area of expertise
        """

    @abstractmethod
    async def evaluate_query(
        self,
        agent_id: str,
        query_text: str,
        existing_tenets: list[Tenet],
        seed_prompt: str,
        role: AgentRole = AgentRole.RESIDENT,
        prophecy: str | None = None,
    ) -> QueryResponse:
        """Evaluate an external query and return a response.

        Unlike proposal evaluation (binary vote), query evaluation produces
        a response text with confidence score and tenet references.
        """
