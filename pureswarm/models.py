"""Core data models for PureSwarm."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _hash_content(*args: Any) -> str:
    """Create a deterministic 12-char hex hash from components."""
    content = ":".join(str(a) for a in args)
    return hashlib.sha256(content.encode()).hexdigest()[:12]


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MessageType(str, Enum):
    PROPOSAL = "proposal"
    VOTE = "vote"
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    REWARD = "reward"
    DOPAMINE = "dopamine"
    PROMPT_GIFT = "prompt_gift"    # true transfer — sender loses tokens
    PROMPT_TRADE = "prompt_trade"  # peer-to-peer swap, any squad


class ProposalStatus(str, Enum):
    PENDING = "pending"
    ADOPTED = "adopted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ProposalAction(str, Enum):
    ADD = "add"
    FUSE = "fuse"
    DELETE = "delete"


class QueryStatus(str, Enum):
    PENDING = "pending"
    DELIBERATING = "deliberating"
    COMPLETED = "completed"
    TIMEOUT = "timeout"


class AgentRole(str, Enum):
    RESIDENT = "resident"
    TRIAD_MEMBER = "triad_member"
    RESEARCHER = "researcher"


class ChronicleCategory(str, Enum):
    GROWTH = "growth"
    PROPHECY = "prophecy"
    CONSENSUS = "consensus"
    MILESTONE = "milestone"
    SPECIALTY = "specialty"
    WORKSHOP = "workshop"


class ProblemDomain(str, Enum):
    """Swarm expertise domains aligned with PureSwarm capabilities."""
    # Core 6 Workshops
    IMMUNE_SYSTEM = "immune_system"      # Autonomous threat detection
    RED_TEAM = "red_team"                # Consensus attack & defense
    SHINOBI = "shinobi"                  # Stealth operations
    CRYPTOGRAPHY = "cryptography"        # Cryptographic authority
    EVOLUTION = "evolution"              # Evolution mechanics
    INFRASTRUCTURE = "infrastructure"    # Distributed architecture
    # Sovereign's Workshop (voluntary)
    SOVEREIGN_CRAFT = "sovereign_craft"  # GovTech Hunter / Saturation Principle


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

class AgentIdentity(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str
    role: AgentRole = AgentRole.RESIDENT
    created_at: datetime = Field(default_factory=_now)
    specialization: str | None = None


# ---------------------------------------------------------------------------
# Tenets (shared beliefs)
# ---------------------------------------------------------------------------

class Tenet(BaseModel):
    id: str = Field(default_factory=_new_id)
    text: str
    proposed_by: str
    adopted_at: datetime = Field(default_factory=_now)
    created_round: int = 0
    source_proposal_id: str | None = None
    votes_for: int = 0
    votes_against: int = 0
    supersedes: list[str] = Field(default_factory=list)  # IDs of tenets replaced by this one
    source_action: Optional[ProposalAction] = None


# ---------------------------------------------------------------------------
# Proposals
# ---------------------------------------------------------------------------

class Proposal(BaseModel):
    id: str = Field(default_factory=_new_id) # Initially random, but can be set deterministically
    tenet_text: str
    proposed_by: str
    action: ProposalAction = ProposalAction.ADD
    target_ids: list[str] = Field(default_factory=list)  # Tenet IDs for FUSE/DELETE
    status: ProposalStatus = ProposalStatus.PENDING
    votes: dict[str, bool] = Field(default_factory=dict)  # agent_id -> yes/no
    created_round: int = 0
    created_at: datetime = Field(default_factory=_now)

    def model_post_init(self, __context: Any) -> None:
        """Lock the ID to the content hash (Requirement #3)."""
        if self.id.startswith("_") or len(self.id) != 12: # only if not already set or it's a default
             self.id = _hash_content(self.tenet_text, self.proposed_by, self.created_round)


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

class Message(BaseModel):
    id: str = Field(default_factory=_new_id)
    sender: str
    type: MessageType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=_now)

    def model_post_init(self, __context: Any) -> None:
        """Traceability without keys (Requirement #3)."""
        if len(self.id) == 24: # uuid hex length is often 32, _new_id is 12. 
            pass # already custom
        # Simple heuristic to overwrite if default
        payload_str = json.dumps(self.payload, sort_keys=True)
        self.id = _hash_content(self.sender, self.type, payload_str, self.timestamp.isoformat())


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

class AuditEntry(BaseModel):
    timestamp: datetime = Field(default_factory=_now)
    agent_id: str
    action: str
    details: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Chronicle (community history)
# ---------------------------------------------------------------------------

class ChronicleEvent(BaseModel):
    """A historical event in the community's collective memory.

    Chronicle events provide context for agent reasoning, allowing them
    to understand the community's evolution and make historically-informed
    decisions.
    """
    round_number: int
    category: ChronicleCategory
    text: str
    timestamp: datetime = Field(default_factory=_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Workshops (real-world problem solving)
# ---------------------------------------------------------------------------

class WorkshopProblem(BaseModel):
    """A real-world societal challenge for the swarm to tackle."""
    id: str = Field(default_factory=_new_id)
    title: str
    description: str
    domain: ProblemDomain
    technical_dimensions: list[str] = Field(default_factory=list)  # e.g., ["distributed systems", "security", "data privacy"]
    ethical_dimensions: list[str] = Field(default_factory=list)    # e.g., ["equity", "transparency", "autonomy"]
    target_specialties: list[str] = Field(default_factory=list)    # Which agent specialties are most relevant


class WorkshopInsight(BaseModel):
    """A discovery or solution from workshop collaboration."""
    agent_id: str
    text: str
    timestamp: datetime = Field(default_factory=_now)


class WorkshopSession(BaseModel):
    """A workshop instance where agents collaborate on a real-world problem."""
    id: str = Field(default_factory=_new_id)
    round_number: int
    problem: WorkshopProblem
    participants: list[str] = Field(default_factory=list)          # Agent IDs
    insights: list[WorkshopInsight] = Field(default_factory=list)  # Collaborative discoveries
    proposals_generated: list[str] = Field(default_factory=list)   # Tenet proposal IDs
    started_at: datetime = Field(default_factory=_now)
    completed_at: datetime | None = None


# ---------------------------------------------------------------------------
# Query Deliberation (external queries to the swarm)
# ---------------------------------------------------------------------------


class QueryResponse(BaseModel):
    """An individual agent's response to an external query."""
    agent_id: str
    response_text: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    tenet_refs: list[str] = Field(default_factory=list)  # IDs of relevant tenets
    specialty: str | None = None  # Agent's specialty if relevant
    timestamp: datetime = Field(default_factory=_now)


class QueryDeliberation(BaseModel):
    """An external query submitted to the swarm for deliberation.

    The swarm receives queries from external channels (Telegram, etc.)
    and agents deliberate to produce a collective response based on
    their shared tenets and individual perspectives.
    """
    id: str = Field(default_factory=_new_id)
    query_text: str
    sender: str
    channel: str  # telegram, discord, http, etc.
    status: QueryStatus = QueryStatus.PENDING
    responses: list[QueryResponse] = Field(default_factory=list)
    final_response: str | None = None
    created_at: datetime = Field(default_factory=_now)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Voting Context (agent awareness before voting)
# ---------------------------------------------------------------------------


class VoteRecord(BaseModel):
    """A record of an agent's past vote and its outcome."""
    proposal_id: str
    action: ProposalAction
    vote: bool  # True = YES, False = NO
    outcome: ProposalStatus  # adopted, rejected, expired
    round_number: int


class VotingContext(BaseModel):
    """Context passed to agents before voting to enable informed decisions.

    This enables agents to vote based on:
    - Community history (chronicle events)
    - Personal experience (lifetime memory)
    - Voting track record (past decisions and outcomes)
    - Squad coordination (Triad recommendations)
    """
    # Chronicle history - recent community events
    recent_events: list[ChronicleEvent] = Field(default_factory=list)
    milestones: list[ChronicleEvent] = Field(default_factory=list)

    # Personal memory - agent's own experiences
    personal_memory: list[str] = Field(default_factory=list)

    # Voting history - past decisions and their outcomes
    voting_history: list[VoteRecord] = Field(default_factory=list)

    # Squad context - Triad findings and recommendations
    squad_id: str | None = None
    triad_recommendations: dict[str, str] = Field(default_factory=dict)  # proposal_id -> "approve"/"reject"
    triad_deliberations: dict[str, str] = Field(default_factory=dict)  # proposal_id -> reasoning text (Phase 5)
    squad_momentum: float = 0.0  # Current squad competition score context


# ---------------------------------------------------------------------------
# Simulation state
# ---------------------------------------------------------------------------

class RoundSummary(BaseModel):
    round_number: int
    proposals_made: int = 0
    votes_cast: int = 0
    tenets_adopted: int = 0
    tenets_rejected: int = 0
    total_tenets: int = 0
    adopted_tenet_texts: list[str] = Field(default_factory=list)


class SimulationReport(BaseModel):
    num_agents: int
    num_rounds: int
    seed_prompt: str
    rounds: list[RoundSummary] = Field(default_factory=list)
    final_tenets: list[Tenet] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=_now)
    finished_at: datetime | None = None
