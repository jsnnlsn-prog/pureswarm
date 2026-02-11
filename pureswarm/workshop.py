"""Workshop system for collective problem-solving on real-world challenges.

The swarm tackles societal problems through collaborative workshops,
applying their technical expertise to climate, healthcare, democracy,
AI ethics, and other critical domains.
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
# Real-World Problem Catalog
# ---------------------------------------------------------------------------

PROBLEM_CATALOG: list[WorkshopProblem] = [
    # Climate & Environment
    WorkshopProblem(
        title="Distributed Climate Data Validation",
        description="How can we build trustworthy, decentralized systems for climate data that prevent manipulation while enabling rapid scientific collaboration?",
        domain=ProblemDomain.CLIMATE,
        technical_dimensions=["distributed systems", "data integrity", "consensus protocols", "blockchain"],
        ethical_dimensions=["transparency", "scientific integrity", "global equity"],
        target_specialties=["cloud", "security", "database", "networking"]
    ),
    WorkshopProblem(
        title="Carbon Footprint Tracking at Scale",
        description="Design systems to accurately track and verify carbon emissions across global supply chains without centralizing control.",
        domain=ProblemDomain.CLIMATE,
        technical_dimensions=["IoT", "distributed ledgers", "data pipelines", "API design"],
        ethical_dimensions=["corporate accountability", "privacy", "data sovereignty"],
        target_specialties=["cloud", "database", "networking", "devops"]
    ),

    # Misinformation & Trust
    WorkshopProblem(
        title="Decentralized Fact-Checking Networks",
        description="How can communities verify information without relying on centralized gatekeepers, while preventing coordinated manipulation?",
        domain=ProblemDomain.MISINFORMATION,
        technical_dimensions=["distributed consensus", "reputation systems", "graph theory", "cryptography"],
        ethical_dimensions=["free speech", "epistemic justice", "power distribution"],
        target_specialties=["security", "database", "networking", "ai_ml"]
    ),
    WorkshopProblem(
        title="Provenance Tracking for Digital Media",
        description="Build systems to track the origin and modification history of images/videos without centralized registries.",
        domain=ProblemDomain.MISINFORMATION,
        technical_dimensions=["cryptographic hashing", "watermarking", "distributed storage", "blockchain"],
        ethical_dimensions=["authenticity", "censorship resistance", "privacy"],
        target_specialties=["security", "cloud", "database"]
    ),

    # Healthcare Access
    WorkshopProblem(
        title="Privacy-Preserving Health Records",
        description="Enable patients to control their medical data while allowing emergency access and research collaboration.",
        domain=ProblemDomain.HEALTHCARE,
        technical_dimensions=["encryption", "access control", "zero-knowledge proofs", "distributed storage"],
        ethical_dimensions=["patient autonomy", "data privacy", "emergency care access"],
        target_specialties=["security", "cloud", "database"]
    ),
    WorkshopProblem(
        title="Telemedicine Infrastructure for Rural Areas",
        description="Design resilient, low-bandwidth systems to deliver healthcare to underserved regions.",
        domain=ProblemDomain.HEALTHCARE,
        technical_dimensions=["edge computing", "network optimization", "offline-first design", "compression"],
        ethical_dimensions=["healthcare equity", "accessibility", "resource allocation"],
        target_specialties=["networking", "cloud", "devops"]
    ),

    # Economic Inequality
    WorkshopProblem(
        title="Transparent Algorithmic Hiring Systems",
        description="Build hiring platforms that are fair and auditable, preventing discriminatory bias while respecting candidate privacy.",
        domain=ProblemDomain.INEQUALITY,
        technical_dimensions=["ML fairness", "explainability", "audit trails", "differential privacy"],
        ethical_dimensions=["fairness", "transparency", "privacy", "accountability"],
        target_specialties=["ai_ml", "security", "database"]
    ),
    WorkshopProblem(
        title="Decentralized Universal Basic Income",
        description="Design distribution systems for UBI that prevent fraud without requiring intrusive surveillance.",
        domain=ProblemDomain.INEQUALITY,
        technical_dimensions=["identity verification", "distributed ledgers", "cryptography", "sybil resistance"],
        ethical_dimensions=["privacy", "dignity", "equity", "autonomy"],
        target_specialties=["security", "database", "networking"]
    ),

    # Privacy vs Security
    WorkshopProblem(
        title="End-to-End Encrypted Collaboration Tools",
        description="Build work platforms with E2E encryption that still allow content moderation and compliance.",
        domain=ProblemDomain.PRIVACY,
        technical_dimensions=["encryption", "key management", "client-side scanning", "metadata protection"],
        ethical_dimensions=["privacy", "safety", "power dynamics", "consent"],
        target_specialties=["security", "cloud", "networking"]
    ),
    WorkshopProblem(
        title="Anonymous Reporting Systems",
        description="Create whistleblower platforms that protect anonymity while preventing abuse and false reports.",
        domain=ProblemDomain.PRIVACY,
        technical_dimensions=["anonymity networks", "reputation systems", "verification", "Tor/mixnets"],
        ethical_dimensions=["accountability", "protection", "trust", "justice"],
        target_specialties=["security", "networking", "database"]
    ),

    # AI Ethics & Governance
    WorkshopProblem(
        title="Auditable AI Decision Systems",
        description="Design AI systems where decisions can be explained and challenged without exposing proprietary models.",
        domain=ProblemDomain.AI_ETHICS,
        technical_dimensions=["explainability", "audit trails", "model cards", "differential privacy"],
        ethical_dimensions=["transparency", "accountability", "fairness", "recourse"],
        target_specialties=["ai_ml", "security", "database"]
    ),
    WorkshopProblem(
        title="Collective Governance of AI Systems",
        description="How can communities democratically govern AI systems that affect them, without technical expertise?",
        domain=ProblemDomain.AI_ETHICS,
        technical_dimensions=["consensus protocols", "voting systems", "accessibility design", "participatory systems"],
        ethical_dimensions=["democracy", "inclusion", "power distribution", "expertise vs democracy"],
        target_specialties=["security", "database", "networking", "frontend"]
    ),

    # Energy & Sustainability
    WorkshopProblem(
        title="Decentralized Energy Grid Management",
        description="Coordinate renewable energy distribution across peer-to-peer grids without central control.",
        domain=ProblemDomain.ENERGY,
        technical_dimensions=["real-time systems", "consensus algorithms", "IoT", "edge computing"],
        ethical_dimensions=["energy democracy", "resilience", "equity", "sustainability"],
        target_specialties=["networking", "cloud", "devops", "iot"]
    ),
    WorkshopProblem(
        title="Sustainable Data Center Design",
        description="Minimize environmental impact of cloud infrastructure while maintaining availability and performance.",
        domain=ProblemDomain.ENERGY,
        technical_dimensions=["workload optimization", "renewable energy", "cooling systems", "efficiency"],
        ethical_dimensions=["environmental responsibility", "cost vs impact", "global inequality"],
        target_specialties=["cloud", "devops", "networking"]
    ),

    # Food Security
    WorkshopProblem(
        title="Transparent Supply Chain Tracking",
        description="Track food from farm to table to reduce waste and ensure safety, without empowering monopolies.",
        domain=ProblemDomain.FOOD_SECURITY,
        technical_dimensions=["IoT", "distributed ledgers", "sensor networks", "data pipelines"],
        ethical_dimensions=["food sovereignty", "fair trade", "transparency", "farmer autonomy"],
        target_specialties=["cloud", "database", "networking", "iot"]
    ),

    # Mental Health
    WorkshopProblem(
        title="Privacy-Preserving Mental Health Platforms",
        description="Build therapy and support systems that protect sensitive data while enabling intervention in crises.",
        domain=ProblemDomain.MENTAL_HEALTH,
        technical_dimensions=["encryption", "access control", "emergency protocols", "local-first design"],
        ethical_dimensions=["privacy", "duty to warn", "autonomy", "care"],
        target_specialties=["security", "cloud", "database", "frontend"]
    ),

    # Democracy & Governance
    WorkshopProblem(
        title="Secure Decentralized Voting Systems",
        description="Build voting systems that are verifiable, anonymous, and resistant to coercion and manipulation.",
        domain=ProblemDomain.DEMOCRACY,
        technical_dimensions=["cryptography", "zero-knowledge proofs", "distributed consensus", "verification"],
        ethical_dimensions=["democracy", "privacy", "accessibility", "trust"],
        target_specialties=["security", "database", "networking"]
    ),
    WorkshopProblem(
        title="Participatory Budgeting Platforms",
        description="Enable communities to democratically allocate resources at scale with transparency and fairness.",
        domain=ProblemDomain.DEMOCRACY,
        technical_dimensions=["voting algorithms", "preference aggregation", "audit trails", "accessibility"],
        ethical_dimensions=["representation", "equity", "deliberation", "power"],
        target_specialties=["database", "security", "frontend"]
    ),

    # Education
    WorkshopProblem(
        title="Decentralized Credential Verification",
        description="Create portable, verifiable educational credentials that don't lock students into platforms.",
        domain=ProblemDomain.EDUCATION,
        technical_dimensions=["distributed identity", "verifiable credentials", "blockchain", "interoperability"],
        ethical_dimensions=["learner autonomy", "credential fraud", "equity", "privacy"],
        target_specialties=["security", "database", "networking"]
    ),

    # Infrastructure
    WorkshopProblem(
        title="Resilient Communication During Disasters",
        description="Build mesh networks and peer-to-peer systems that maintain connectivity when infrastructure fails.",
        domain=ProblemDomain.INFRASTRUCTURE,
        technical_dimensions=["mesh networking", "offline-first", "edge computing", "resilience"],
        ethical_dimensions=["emergency access", "equity", "decentralization", "public good"],
        target_specialties=["networking", "cloud", "devops"]
    ),
]


# ---------------------------------------------------------------------------
# Workshop Orchestrator
# ---------------------------------------------------------------------------

class WorkshopOrchestrator:
    """Manages workshop selection, execution, and insight tracking."""

    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._catalog = PROBLEM_CATALOG
        self._history: list[WorkshopSession] = []

    async def select_problem(
        self,
        round_number: int,
        agent_specialties: list[str],
        chronicle_events: list[Any] | None = None,
        sovereign_override: str | None = None
    ) -> WorkshopProblem:
        """Select the next workshop problem.

        Selection strategy (Hybrid - Option C):
        1. Sovereign override via prophecy (highest priority)
        2. Chronicle-driven (respond to recent patterns)
        3. Specialty-matched (ensure relevance to current agents)
        4. Rotating curriculum (ensure diversity)
        """

        # Sovereign override
        if sovereign_override:
            for problem in self._catalog:
                if sovereign_override.lower() in problem.title.lower():
                    logger.info("Workshop: Sovereign mandate - %s", problem.title)
                    return problem

        # Chronicle-driven selection (check for patterns in recent events)
        if chronicle_events:
            # Example: If many consensus events, focus on democracy/governance
            # Example: If growth events, focus on scalability/infrastructure
            # This can be expanded with sophisticated pattern matching
            pass

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
        domain_counts = {}
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
        # For now, return workshop problem as a tenet proposal template
        # In full implementation, this would use agent reasoning to synthesize insights
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
        # Template-based synthesis (can be enhanced with agent reasoning)
        templates = {
            ProblemDomain.CLIMATE: "Systems addressing {title} must prioritize {ethical} while implementing {technical}",
            ProblemDomain.MISINFORMATION: "To combat {title}, we must balance {ethical} with {technical} approaches",
            ProblemDomain.HEALTHCARE: "Healthcare solutions for {title} require {technical} infrastructure that honors {ethical}",
            ProblemDomain.INEQUALITY: "Addressing {title} demands {technical} systems designed with {ethical} at their core",
            ProblemDomain.PRIVACY: "Privacy-preserving approaches to {title} must integrate {technical} and respect {ethical}",
            ProblemDomain.AI_ETHICS: "AI systems for {title} require {technical} capabilities governed by {ethical} principles",
            ProblemDomain.ENERGY: "Sustainable solutions to {title} need {technical} innovation aligned with {ethical}",
            ProblemDomain.FOOD_SECURITY: "Food systems addressing {title} should combine {technical} with commitment to {ethical}",
            ProblemDomain.MENTAL_HEALTH: "Mental health platforms for {title} must balance {technical} security with {ethical}",
            ProblemDomain.DEMOCRACY: "Democratic systems for {title} require {technical} robustness and {ethical} foundations",
            ProblemDomain.EDUCATION: "Educational technology for {title} should leverage {technical} while ensuring {ethical}",
            ProblemDomain.INFRASTRUCTURE: "Infrastructure solutions for {title} need {technical} resilience rooted in {ethical}",
        }

        template = templates.get(problem.domain, "Solutions to {title} require {technical} and {ethical}")

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
