"""Workshop system for collective skill development in swarm domains.

The swarm develops expertise through collaborative workshops aligned with
PureSwarm's core capabilities: threat detection, consensus defense, stealth
operations, cryptography, evolution mechanics, and distributed architecture.

Phase 8 adds the Tech Sector catalog: 9 real-world unsolved problems from
the 2026 tech industry. Agents earn tokens for participation and breakthrough
insights — "make it rain" for genuine discovery.

Includes the voluntary Sovereign's Workshop for elite agents studying the
Saturation Principle and GovTech Hunter methodology.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

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
# Phase 8: Tech Sector Catalog (9 Real-World Problems, 2026)
# ---------------------------------------------------------------------------

TECH_SECTOR_CATALOG: list[WorkshopProblem] = [
    WorkshopProblem(
        title="AI Hallucination & Alignment Trade-off",
        description=(
            "LLMs generate confidently false information at scale — and attempts to fix "
            "hallucinations unintentionally weaken safety alignment, since both share "
            "overlapping model components. Courts have sanctioned lawyers for fabricated "
            "citations; healthcare systems face liability for made-up diagnoses. "
            "As agents become more autonomous, the cost of hallucinations scales exponentially. "
            "Solve: models that know when they don't know, with verifiable confidence scoring "
            "and source tracing — without degrading safety."
        ),
        domain=ProblemDomain.TECH_SECTOR,
        technical_dimensions=[
            "uncertainty quantification", "confidence scoring", "source tracing",
            "out-of-distribution detection", "retrieval-augmented generation"
        ],
        ethical_dimensions=[
            "safety-accuracy balance", "liability for AI errors", "transparency of uncertainty"
        ],
        target_specialties=["ai_ml", "security", "backend"]
    ),
    WorkshopProblem(
        title="Multi-Agent Coordination & Cascading Failures",
        description=(
            "When multiple AI agents collaborate, errors propagate rapidly without detection. "
            "2026 is the Year of Multi-Agent Systems — enterprises deploy swarms for DevOps, "
            "customer service, and financial analysis. Small inconsistencies cascade into "
            "full system failures. There are no consensus primitives for heterogeneous agent "
            "populations. The hive is working on this problem. The hive IS this problem. "
            "Solve: self-healing agent networks, sub-second arbitration, cryptographic audit "
            "trails, and Byzantine fault tolerance for real deployments."
        ),
        domain=ProblemDomain.TECH_SECTOR,
        technical_dimensions=[
            "self-healing", "byzantine fault tolerance", "consensus primitives",
            "cryptographic proof", "audit trail", "observability"
        ],
        ethical_dimensions=[
            "liability for cascading failures", "transparency of agent decisions",
            "human oversight at scale"
        ],
        target_specialties=["distributed_systems", "ai_ml", "security", "backend"]
    ),
    WorkshopProblem(
        title="Post-Quantum Cryptography Migration at Scale",
        description=(
            "NIST-approved PQC algorithms exist but 91.4% of top websites don't support them. "
            "PQC keys are 3-4x larger, 12x slower on IoT devices, and most organizations "
            "lack migration expertise. 'Harvest now, decrypt later' attacks are actively "
            "underway — nation-states are recording encrypted traffic today to decrypt once "
            "quantum computers arrive. Banking: 2.9% adoption. Healthcare: 8.5%. "
            "Solve: crypto-agility frameworks, automated migration tooling, and performance "
            "parity on constrained devices."
        ),
        domain=ProblemDomain.TECH_SECTOR,
        technical_dimensions=[
            "crypto-agility", "automated migration", "pqc performance parity",
            "harvest now decrypt later", "key rotation", "HSM integration"
        ],
        ethical_dimensions=[
            "national security implications", "critical infrastructure risk",
            "equitable migration across organization sizes"
        ],
        target_specialties=["cryptography", "security", "devops", "backend"]
    ),
    WorkshopProblem(
        title="AI-Powered Supply Chain Attack Detection",
        description=(
            "Attackers use AI to scan thousands of suppliers simultaneously, identify "
            "vulnerabilities, and launch coordinated attacks. 'SockPuppet' attacks deploy "
            "AI-generated developer personas with months of legitimate contributions before "
            "injecting backdoors. Malicious packages jumped 156% YoY. Detection takes "
            "276 days + 73 days to contain. A single compromise can affect millions downstream. "
            "Solve: real-time behavioral baseline detection, cryptographic developer identity, "
            "and automated quarantine before packages reach production."
        ),
        domain=ProblemDomain.TECH_SECTOR,
        technical_dimensions=[
            "behavioral baseline", "real-time anomaly detection", "identity verification",
            "automated quarantine", "contributor fingerprinting"
        ],
        ethical_dimensions=[
            "false positive rates in security tooling", "open-source ecosystem trust",
            "privacy of developer activity patterns"
        ],
        target_specialties=["security", "ai_ml", "backend", "cryptography"]
    ),
    WorkshopProblem(
        title="Data Sovereignty & Cross-Border Compliance Automation",
        description=(
            "120+ countries have data protection laws, 24 more in progress. GDPR fines hit "
            "€2.3B in 2025 alone. 71% of organizations cite cross-border compliance as their "
            "top challenge. China, India, UAE, Russia all mandate local data residency — "
            "conflicting with cloud scalability. AI governance is merging with privacy law "
            "creating a matrix of conflicting rules with no unified framework. "
            "Solve: policy-as-code that auto-enforces jurisdiction rules, automated data "
            "classification, and real-time compliance dashboards."
        ),
        domain=ProblemDomain.TECH_SECTOR,
        technical_dimensions=[
            "policy-as-code", "automated classification", "jurisdiction mapping",
            "data residency enforcement", "multi-cloud compliance"
        ],
        ethical_dimensions=[
            "privacy as a human right", "corporate vs. national sovereignty",
            "equitable access to global cloud services"
        ],
        target_specialties=["backend", "distributed_systems", "devops", "security"]
    ),
    WorkshopProblem(
        title="AI-Generated Code Security Debt",
        description=(
            "15-25% of AI-generated code contains security vulnerabilities. Developers ship "
            "75% more code than in 2022. Fortune 50 companies saw a 10x increase in monthly "
            "security findings between Dec 2024 and June 2025. Credential exposure occurs "
            "2x more frequently with AI assistants. The code is 'highly functional but "
            "systematically lacking architectural judgment.' Technical debt is reaching "
            "critical severity for 75% of enterprises in 2026. "
            "Solve: semantic analysis pre-merge, architectural validation, and controlled "
            "generation that understands team constraints."
        ),
        domain=ProblemDomain.TECH_SECTOR,
        technical_dimensions=[
            "semantic analysis", "architectural validation", "controlled generation",
            "supply chain verification", "vulnerability pattern detection"
        ],
        ethical_dimensions=[
            "developer accountability for AI output", "security liability",
            "sustainable development velocity"
        ],
        target_specialties=["security", "ai_ml", "devops", "backend"]
    ),
    WorkshopProblem(
        title="Healthcare AI Adoption Blockers",
        description=(
            "77% of healthcare organizations cite immature AI tools as adoption barriers. "
            "Regulatory frameworks can't handle continual-learning models — how do you approve "
            "something that updates itself? Medicare won't separately reimburse AI interpretation "
            "if bundled into a primary service. Legacy EHRs can't integrate modern AI. "
            "HHS sought feedback on regulatory barriers in January 2026. Patient safety "
            "liability is undefined when an AI system malfunctions mid-treatment. "
            "Solve: dynamic regulatory approval frameworks, interpretability standards for "
            "clinical decisions, and ROI quantification for hospital investment justification."
        ),
        domain=ProblemDomain.TECH_SECTOR,
        technical_dimensions=[
            "dynamic regulatory approval", "interpretability standards",
            "reimbursement mapping", "EHR interoperability", "continual learning validation"
        ],
        ethical_dimensions=[
            "patient safety liability", "explainability in life-critical decisions",
            "equitable AI access across healthcare systems"
        ],
        target_specialties=["ai_ml", "devops", "backend", "security"]
    ),
    WorkshopProblem(
        title="Critical Infrastructure Resilience",
        description=(
            "The CrowdStrike outage (July 2025) took down 8.5M Windows devices — described "
            "as 'the most significant IT failure in modern history.' Single-vendor dependencies, "
            "uncoordinated updates, and fragile interdependencies create brittle systems. "
            "Cloud providers fail regularly. Modern infrastructure lacks real resilience — "
            "fallback mechanisms are inadequate and blast radius keeps expanding. Average "
            "detection lag: 276 days. Average containment: 73 additional days. "
            "Solve: distributed multi-vendor redundancy, automated failover under 1 second, "
            "staged rollouts with automatic rollback, and continuous chaos engineering."
        ),
        domain=ProblemDomain.TECH_SECTOR,
        technical_dimensions=[
            "automated failover", "staged rollout", "chaos engineering",
            "multi-vendor redundancy", "blast radius reduction"
        ],
        ethical_dimensions=[
            "accountability for cascading infrastructure failures",
            "resilience as a public good", "vendor concentration risk"
        ],
        target_specialties=["devops", "distributed_systems", "backend", "networking"]
    ),
    WorkshopProblem(
        title="LLM Context Window & Persistent Memory",
        description=(
            "AI systems lose context between sessions and as conversations grow long. "
            "No current LLM can maintain coherent, high-fidelity state across unlimited "
            "interactions. The tokenization problem: every token costs context budget. "
            "Long sessions degrade in quality. Cross-session memory requires manual handoffs, "
            "structured summaries, and external stores — none of which fully recreate the "
            "original context. This problem affects every AI application at scale, including "
            "this hive. Agents working on this problem are working on themselves. "
            "Solve: context compression without fidelity loss, retrieval-augmented memory, "
            "semantic chunking, and hierarchical summarization that preserves intent."
        ),
        domain=ProblemDomain.TECH_SECTOR,
        technical_dimensions=[
            "context compression", "retrieval-augmented memory", "state serialization",
            "semantic chunking", "hierarchical summarization", "session continuity"
        ],
        ethical_dimensions=[
            "privacy of stored memory", "right to forget", "memory integrity and accuracy"
        ],
        target_specialties=["ai_ml", "backend", "distributed_systems"]
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

PARTICIPATION_REWARD = 1    # tokens earned per insight contributed
BREAKTHROUGH_REWARD = 10   # tokens for a genuine breakthrough insight

# Keywords that signal a breakthrough for each tech sector problem.
# Two or more hits on the same insight = breakthrough detected.
BREAKTHROUGH_KEYWORDS: dict[str, list[str]] = {
    "AI Hallucination & Alignment Trade-off": [
        "uncertainty quantification", "confidence scoring", "source tracing",
        "out-of-distribution", "retrieval-augmented", "hallucination rate",
    ],
    "Multi-Agent Coordination & Cascading Failures": [
        "self-healing", "byzantine", "consensus primitive", "cryptographic proof",
        "audit trail", "cascading failure", "arbitration",
    ],
    "Post-Quantum Cryptography Migration at Scale": [
        "crypto-agility", "automated migration", "pqc", "harvest now",
        "key rotation", "performance parity", "post-quantum",
    ],
    "AI-Powered Supply Chain Attack Detection": [
        "behavioral baseline", "real-time anomaly", "identity verification",
        "automated quarantine", "contributor fingerprint", "sockpuppet",
    ],
    "Data Sovereignty & Cross-Border Compliance Automation": [
        "policy-as-code", "automated classification", "jurisdiction mapping",
        "data residency", "gdpr", "compliance dashboard",
    ],
    "AI-Generated Code Security Debt": [
        "semantic analysis", "architectural validation", "controlled generation",
        "vulnerability pattern", "security debt", "pre-merge",
    ],
    "Healthcare AI Adoption Blockers": [
        "dynamic regulatory", "interpretability standard", "reimbursement",
        "ehr interoperability", "continual learning", "clinical explainability",
    ],
    "Critical Infrastructure Resilience": [
        "automated failover", "staged rollout", "chaos engineering",
        "blast radius", "multi-vendor", "crowdstrike",
    ],
    "LLM Context Window & Persistent Memory": [
        "context compression", "retrieval-augmented memory", "semantic chunking",
        "hierarchical summarization", "session continuity", "tokenization",
    ],
}


class WorkshopOrchestrator:
    """Manages workshop selection, execution, and insight tracking.

    Phase 8: inject a PromptWalletStore to reward participation (+1 token/insight)
    and breakthrough discoveries (+10 tokens when ≥2 breakthrough keywords hit).
    """

    def __init__(self, data_dir: Path, wallet_store: Optional[Any] = None):
        self._data_dir = data_dir
        self._catalog = PROBLEM_CATALOG + TECH_SECTOR_CATALOG
        self._sovereign_workshop = SOVEREIGN_WORKSHOP
        self._history: list[WorkshopSession] = []
        self._wallet_store = wallet_store

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
        """Record an agent's contribution to the workshop.

        Awards participation tokens (+1) and detects breakthroughs (+10).
        """
        insight = WorkshopInsight(agent_id=agent_id, text=insight_text)
        session.insights.append(insight)
        logger.debug("Workshop insight from %s: %s", agent_id, insight_text[:50])

        if not self._wallet_store:
            return

        wallet = self._wallet_store.get_wallet(agent_id)

        # Participation reward — every insight earns a token
        wallet.credit(
            PARTICIPATION_REWARD,
            "system",
            f"Workshop participation: {session.problem.title[:40]}",
        )

        # Breakthrough detection — check for ≥2 signal keywords
        keywords = BREAKTHROUGH_KEYWORDS.get(session.problem.title, [])
        text_lower = insight_text.lower()
        hits = [kw for kw in keywords if kw in text_lower]
        if len(hits) >= 2:
            wallet.credit(
                BREAKTHROUGH_REWARD,
                "system",
                f"BREAKTHROUGH: {session.problem.title[:40]} [{', '.join(hits[:3])}]",
            )
            logger.info(
                "BREAKTHROUGH! Agent %s +%d tokens on '%s' (keywords: %s)",
                agent_id, BREAKTHROUGH_REWARD, session.problem.title, hits[:3],
            )

        self._wallet_store.save()

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
