"""Core data models for PureSwarm."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

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


class ProposalStatus(str, Enum):
    PENDING = "pending"
    ADOPTED = "adopted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AgentRole(str, Enum):
    RESIDENT = "resident"
    TRIAD_MEMBER = "triad_member"


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


# ---------------------------------------------------------------------------
# Proposals
# ---------------------------------------------------------------------------

class Proposal(BaseModel):
    id: str = Field(default_factory=_new_id) # Initially random, but can be set deterministically
    tenet_text: str
    proposed_by: str
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
