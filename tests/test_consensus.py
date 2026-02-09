"""Tests for the consensus protocol."""

import asyncio
import pytest
from pathlib import Path
from pureswarm.consensus import ConsensusProtocol
from pureswarm.memory import SharedMemory
from pureswarm.models import Proposal
from pureswarm.security import AuditLogger


@pytest.fixture
def setup(tmp_path):
    audit = AuditLogger(tmp_path / "logs")
    mem = SharedMemory(tmp_path, audit)
    consensus = ConsensusProtocol(
        shared_memory=mem,
        audit_logger=audit,
        num_agents=3,
        approval_threshold=0.5,
        proposal_expiry_rounds=3,
        max_active_proposals=5,
    )
    return consensus, mem


@pytest.mark.asyncio
async def test_proposal_adopted(setup):
    consensus, mem = setup
    p = Proposal(tenet_text="We shall seek truth", proposed_by="a1", created_round=1)
    assert consensus.submit_proposal(p)

    # 2 out of 2 non-proposer agents vote yes
    consensus.cast_vote("a2", p.id, True)
    consensus.cast_vote("a3", p.id, True)

    adopted = await consensus.end_of_round(1)
    assert len(adopted) == 1
    assert adopted[0].text == "We shall seek truth"

    tenets = await mem.read_tenets()
    assert len(tenets) == 1


@pytest.mark.asyncio
async def test_proposal_rejected(setup):
    consensus, mem = setup
    p = Proposal(tenet_text="Bad idea", proposed_by="a1", created_round=1)
    consensus.submit_proposal(p)

    consensus.cast_vote("a2", p.id, False)
    consensus.cast_vote("a3", p.id, False)

    adopted = await consensus.end_of_round(1)
    assert len(adopted) == 0
    assert len(await mem.read_tenets()) == 0


@pytest.mark.asyncio
async def test_proposal_expires(setup):
    consensus, mem = setup
    p = Proposal(tenet_text="Old proposal", proposed_by="a1", created_round=1)
    consensus.submit_proposal(p)

    # Don't vote, let it expire after 3 rounds
    for r in range(1, 5):
        await consensus.end_of_round(r)

    assert p.status.value == "expired"


@pytest.mark.asyncio
async def test_duplicate_vote_rejected(setup):
    consensus, _ = setup
    p = Proposal(tenet_text="Test", proposed_by="a1", created_round=1)
    consensus.submit_proposal(p)

    assert consensus.cast_vote("a2", p.id, True) is True
    assert consensus.cast_vote("a2", p.id, False) is False  # duplicate


@pytest.mark.asyncio
async def test_max_active_limit(setup):
    consensus, _ = setup
    for i in range(5):
        p = Proposal(tenet_text=f"Proposal {i}", proposed_by="a1", created_round=1)
        assert consensus.submit_proposal(p) is True

    # 6th should fail
    p = Proposal(tenet_text="One too many", proposed_by="a1", created_round=1)
    assert consensus.submit_proposal(p) is False
