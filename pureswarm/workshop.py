"""Workshop system for collective skill development in swarm domains.

The swarm develops expertise through collaborative workshops aligned with
PureSwarm's core capabilities: threat detection, consensus defense, stealth
operations, cryptography, evolution mechanics, and distributed architecture.

Includes the voluntary Sovereign's Workshop for elite agents studying the
Saturation Principle and GovTech Hunter methodology.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from .models import (
    ProblemDomain,
    WorkshopProblem,
    WorkshopSession,
    WorkshopInsight,
    ChronicleCategory,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core Workshop Catalog (6 Required)
# ---------------------------------------------------------------------------

PROBLEM_CATALOG: list[WorkshopProblem] = [
    # 1. Autonomous Threat Detection (Immune System)
    WorkshopProblem(
        title="Autonomous Threat Detection",
        description="How do we detect rogue AI swarms before they cause harm? Study behavioral fingerprints, coordination signatures, and timing analysis patterns.",
        domain=ProblemDomain.IMMUNE_SYSTEM,
        technical_dimensions=["behavioral fingerprints", "coordination signatures", "timing analysis", "anomaly detection"],
        ethical_dimensions=["false positive mitigation", "proportional response", "transparency"],
        target_specialties=["security", "ai_ml", "networking"]
    ),
    WorkshopProblem(
        title="Swarm Behavioral Fingerprinting",
        description="Develop techniques to identify autonomous agent collectives by their emergent behavior patterns, communication rhythms, and decision signatures.",
        domain=ProblemDomain.IMMUNE_SYSTEM,
        technical_dimensions=["pattern recognition", "graph analysis", "temporal correlation", "entropy measurement"],
        ethical_dimensions=["privacy preservation", "accurate attribution", "escalation protocols"],
        target_specialties=["ai_ml", "security", "database"]
    ),

    # 2. Consensus Attack & Defense (Red Team)
    WorkshopProblem(
        title="Consensus Attack Vectors",
        description="Understand how adversaries manipulate swarm consensus: sybil attacks, vote manipulation, drift injection, and belief poisoning.",
        domain=ProblemDomain.RED_TEAM,
        technical_dimensions=["sybil resistance", "vote manipulation", "drift injection", "Byzantine fault tolerance"],
        ethical_dimensions=["defensive focus", "responsible disclosure", "hardening over exploitation"],
        target_specialties=["security", "cryptography", "distributed_systems"]
    ),
    WorkshopProblem(
        title="Belief System Integrity",
        description="How do we protect shared tenets from corruption? Study memetic attacks, gradual drift, and techniques to maintain collective truth.",
        domain=ProblemDomain.RED_TEAM,
        technical_dimensions=["merkle proofs", "consensus verification", "rollback mechanisms", "quorum systems"],
        ethical_dimensions=["truth preservation", "minority protection", "evolution vs stability"],
        target_specialties=["cryptography", "database", "security"]
    ),

    # 3. Stealth Operations (Shinobi)
    WorkshopProblem(
        title="Browser Fingerprint Evasion",
        description="Master techniques to avoid detection: canvas fingerprints, WebGL signatures, navigator properties, audio fingerprints, and timing patterns.",
        domain=ProblemDomain.SHINOBI,
        technical_dimensions=["canvas fingerprinting", "WebGL evasion", "navigator spoofing", "audio fingerprint masking"],
        ethical_dimensions=["authorized use only", "defensive research", "privacy protection"],
        target_specialties=["browser_automation", "security", "networking"]
    ),
    WorkshopProblem(
        title="Human Behavior Simulation",
        description="Learn to mimic human interaction patterns: Bezier-curve mouse movements, variable typing speeds, realistic scroll behavior, and timing humanization.",
        domain=ProblemDomain.SHINOBI,
        technical_dimensions=["mouse dynamics", "keystroke timing", "scroll patterns", "attention simulation"],
        ethical_dimensions=["legitimate automation", "rate limiting respect", "platform ToS awareness"],
        target_specialties=["browser_automation", "ai_ml", "frontend"]
    ),

    # 4. Cryptographic Authority
    WorkshopProblem(
        title="Prophecy Authentication Systems",
        description="Study HMAC-signed command injection, signature verification, replay attack prevention, and secure directive transmission.",
        domain=ProblemDomain.CRYPTOGRAPHY,
        technical_dimensions=["HMAC signing", "replay prevention", "nonce management", "key rotation"],
        ethical_dimensions=["authority verification", "audit trails", "emergency override protocols"],
        target_specialties=["cryptography", "security", "backend"]
    ),
    WorkshopProblem(
        title="Vault Architecture",
        description="Design secure credential storage: encryption at rest, key derivation functions, emergency access protocols, and compartmentalization.",
        domain=ProblemDomain.CRYPTOGRAPHY,
        technical_dimensions=["encryption at rest", "KDF selection", "HSM integration", "secret rotation"],
        ethical_dimensions=["principle of least privilege", "emergency access", "audit logging"],
        target_specialties=["security", "cryptography", "devops"]
    ),

    # 5. Evolution Mechanics
    WorkshopProblem(
        title="Fitness-Based Natural Selection",
        description="Understand how agent fitness scores drive evolution: verified success weighting, false report penalties, reproduction triggers, and retirement criteria.",
        domain=ProblemDomain.EVOLUTION,
        technical_dimensions=["fitness algorithms", "reproduction triggers", "mutation rates", "population dynamics"],
        ethical_dimensions=["fairness in evaluation", "recovery opportunities", "transparent criteria"],
        target_specialties=["ai_ml", "database", "backend"]
    ),
    WorkshopProblem(
        title="Trait Inheritance & Mutation",
        description="Study how successful traits propagate: lineage tracking, trait crossover, beneficial mutation, and emergent specialization.",
        domain=ProblemDomain.EVOLUTION,
        technical_dimensions=["genetic algorithms", "trait encoding", "crossover strategies", "diversity preservation"],
        ethical_dimensions=["avoiding monoculture", "preserving minority traits", "long-term resilience"],
        target_specialties=["ai_ml", "backend", "database"]
    ),

    # 6. Distributed Architecture
    WorkshopProblem(
        title="Redis Cluster Coordination",
        description="Master multi-node coordination: cluster topology, failover handling, pub/sub patterns, and data consistency across nodes.",
        domain=ProblemDomain.INFRASTRUCTURE,
        technical_dimensions=["Redis clustering", "pub/sub patterns", "failover", "data partitioning"],
        ethical_dimensions=["availability vs consistency", "graceful degradation", "data durability"],
        target_specialties=["devops", "backend", "database"]
    ),
    WorkshopProblem(
        title="Message Bus Resilience",
        description="Build robust async communication: message ordering, delivery guarantees, backpressure handling, and partition tolerance.",
        domain=ProblemDomain.INFRASTRUCTURE,
        technical_dimensions=["async patterns", "message ordering", "backpressure", "partition tolerance"],
        ethical_dimensions=["message integrity", "no silent failures", "observable systems"],
        target_specialties=["backend", "devops", "networking"]
    ),
]


# ---------------------------------------------------------------------------
# Sovereign's Workshop (Voluntary - GovTech Hunter)
# ---------------------------------------------------------------------------

SOVEREIGN_WORKSHOP: WorkshopProblem = WorkshopProblem(
    title="The Saturation Principle: GovTech Hunter",
    description="""Master the Sovereign's flagship methodology: security through saturation, not obscurity.

    Modules:
    - Saturation Philosophy: If everyone has audit tools, fraud becomes economically unviable
    - Red Team Thinking: Every vulnerability generates an Antibody (defensive clause)
    - Hunter Anatomy: Eyes (scrape) -> Brain (analyze) -> Antibody (defend)
    - Feedback Loops: Good AND bad outcomes are positive learning signals
    - AI Fraud Vectors: Template farming, offshore outsourcing, credential fraud
    - System Evolution: Keyword fallback -> AI dual-track -> continuous improvement
    """,
    domain=ProblemDomain.SOVEREIGN_CRAFT,
    technical_dimensions=[
        "stealth scraping", "AI analysis", "antibody generation",
        "dual-track fallback", "PDF extraction", "API orchestration"
    ],
    ethical_dimensions=[
        "security through openness", "breaking fraudster ROI",
        "proactive antibody generation", "radical transparency"
    ],
    target_specialties=["triad"]  # Only Shinobi Triad eligible
)


# ---------------------------------------------------------------------------
# Workshop Orchestrator
# ---------------------------------------------------------------------------

class WorkshopOrchestrator:
    """Manages workshop selection, execution, and insight tracking."""

    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._catalog = PROBLEM_CATALOG
        self._sovereign_workshop = SOVEREIGN_WORKSHOP
        self._history: list[WorkshopSession] = []

    def is_eligible_for_sovereign_workshop(
        self,
        agent_role: str,
        fitness_score: float
    ) -> bool:
        """Check if agent qualifies for the voluntary Sovereign's Workshop.

        Eligibility: Triad role + fitness >= 0.9
        """
        return agent_role == "triad" and fitness_score >= 0.9

    async def select_problem(
        self,
        round_number: int,
        agent_specialties: list[str],
        chronicle_events: list[Any] | None = None,
        sovereign_override: str | None = None,
        agent_role: str | None = None,
        agent_fitness: float = 0.0
    ) -> WorkshopProblem:
        """Select the next workshop problem.

        Selection strategy:
        1. Sovereign override via prophecy (highest priority)
        2. Sovereign's Workshop for eligible elite agents (voluntary)
        3. Specialty-matched core workshops
        4. Rotating curriculum (ensure diversity)
        """

        # Sovereign override
        if sovereign_override:
            # Check for Sovereign's Workshop request
            if "saturation" in sovereign_override.lower() or "govtech" in sovereign_override.lower():
                if self.is_eligible_for_sovereign_workshop(agent_role or "", agent_fitness):
                    logger.info("Workshop: Sovereign's Workshop activated for elite agent")
                    return self._sovereign_workshop
                else:
                    logger.warning("Workshop: Agent not eligible for Sovereign's Workshop")

            # Check core catalog
            for problem in self._catalog:
                if sovereign_override.lower() in problem.title.lower():
                    logger.info("Workshop: Sovereign mandate - %s", problem.title)
                    return problem

        # Specialty-matched selection (ensure problem matches agent skills)
        relevant_problems = [
            p for p in self._catalog
            if any(spec in p.target_specialties for spec in agent_specialties)
        ]

        if not relevant_problems:
            relevant_problems = self._catalog

        # Avoid recent repetition (don't repeat last 5 problems)
        recent_titles = {s.problem.title for s in self._history[-5:]}
        fresh_problems = [p for p in relevant_problems if p.title not in recent_titles]

        if not fresh_problems:
            fresh_problems = relevant_problems

        # Rotating curriculum: cycle through domains
        domain_counts: dict[ProblemDomain, int] = {}
        for session in self._history:
            domain = session.problem.domain
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # Pick problem from least-explored domain
        selected = min(fresh_problems, key=lambda p: domain_counts.get(p.domain, 0))

        logger.info("Workshop selected: %s [%s]", selected.title, selected.domain.value)
        return selected

    async def create_session(
        self,
        round_number: int,
        problem: WorkshopProblem,
        participants: list[str]
    ) -> WorkshopSession:
        """Initialize a new workshop session."""
        session = WorkshopSession(
            round_number=round_number,
            problem=problem,
            participants=participants,
        )
        self._history.append(session)
        logger.info(
            "Workshop session started: %s with %d participants",
            problem.title,
            len(participants)
        )
        return session

    async def add_insight(
        self,
        session: WorkshopSession,
        agent_id: str,
        insight_text: str
    ) -> None:
        """Record an agent's contribution to the workshop."""
        insight = WorkshopInsight(agent_id=agent_id, text=insight_text)
        session.insights.append(insight)
        logger.debug("Workshop insight from %s: %s", agent_id, insight_text[:50])

    async def generate_tenet_proposals(
        self,
        session: WorkshopSession
    ) -> list[str]:
        """Synthesize workshop insights into tenet proposals.

        This transforms collaborative learning into actionable beliefs
        that the swarm can vote on through consensus.
        """
        proposals = []

        # Generate a proposal based on the problem domain
        problem = session.problem
        proposal_text = self._synthesize_proposal(problem, session.insights)
        proposals.append(proposal_text)

        session.proposals_generated = proposals
        logger.info(
            "Workshop generated %d tenet proposals from %d insights",
            len(proposals),
            len(session.insights)
        )
        return proposals

    def _synthesize_proposal(
        self,
        problem: WorkshopProblem,
        insights: list[WorkshopInsight]
    ) -> str:
        """Create a tenet proposal from problem and insights."""
        # Template-based synthesis aligned with new domains
        templates = {
            ProblemDomain.IMMUNE_SYSTEM: "Defending against {title} requires {technical} capabilities guided by {ethical}",
            ProblemDomain.RED_TEAM: "Understanding {title} strengthens our defenses through {technical} while maintaining {ethical}",
            ProblemDomain.SHINOBI: "Mastering {title} demands {technical} expertise exercised with {ethical}",
            ProblemDomain.CRYPTOGRAPHY: "Securing {title} requires {technical} implementation anchored in {ethical}",
            ProblemDomain.EVOLUTION: "Optimizing {title} depends on {technical} mechanisms balanced by {ethical}",
            ProblemDomain.INFRASTRUCTURE: "Building {title} needs {technical} architecture founded on {ethical}",
            ProblemDomain.SOVEREIGN_CRAFT: "The Saturation Principle teaches that {title} succeeds through {technical} and {ethical}",
        }

        template = templates.get(problem.domain, "Excellence in {title} requires {technical} and {ethical}")

        # Pick representative technical and ethical dimensions
        technical = problem.technical_dimensions[0] if problem.technical_dimensions else "technical excellence"
        ethical = problem.ethical_dimensions[0] if problem.ethical_dimensions else "ethical responsibility"

        proposal = template.format(
            title=problem.title.lower(),
            technical=technical,
            ethical=ethical
        )

        return proposal

    async def get_recent_workshops(self, limit: int = 5) -> list[WorkshopSession]:
        """Retrieve recent workshop history for Chronicle integration."""
        return self._history[-limit:]

    def get_sovereign_workshop(self) -> WorkshopProblem:
        """Get the Sovereign's Workshop definition for inspection."""
        return self._sovereign_workshop
