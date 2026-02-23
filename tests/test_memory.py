"""Tests for consensus-gated shared memory."""

import asyncio
import pytest
from pathlib import Path
from pureswarm.memory import SharedMemory, CONSENSUS_GUARD
from pureswarm.models import Tenet
from pureswarm.security import AuditLogger


@pytest.fixture
def tmp_data(tmp_path):
    audit = AuditLogger(tmp_path / "logs")
    mem = SharedMemory(tmp_path, audit)
    return mem


@pytest.mark.asyncio
async def test_read_empty(tmp_data):
    tenets = await tmp_data.read_tenets()
    assert tenets == []


@pytest.mark.asyncio
async def test_write_with_sentinel(tmp_data):
    tenet = Tenet(text="Test tenet", proposed_by="agent-1")
    await tmp_data.write_tenet(tenet, _auth=CONSENSUS_GUARD)
    tenets = await tmp_data.read_tenets()
    assert len(tenets) == 1
    assert tenets[0].text == "Test tenet"


@pytest.mark.asyncio
async def test_write_without_sentinel_raises(tmp_data):
    tenet = Tenet(text="Sneaky write", proposed_by="agent-1")
    with pytest.raises(PermissionError):
        await tmp_data.write_tenet(tenet)


@pytest.mark.asyncio
async def test_archive_created(tmp_data):
    tenet = Tenet(text="Archived tenet", proposed_by="agent-1")
    await tmp_data.write_tenet(tenet, _auth=CONSENSUS_GUARD)
    archive_dir = tmp_data._archive_dir
    archives = list(archive_dir.glob("tenets_*.json"))
    assert len(archives) >= 1


@pytest.mark.asyncio
async def test_reset_preserves_tenets(tmp_data):
    """Reset is now a no-op that preserves tenets across simulation runs."""
    tenet = Tenet(text="Will be preserved", proposed_by="agent-1")
    await tmp_data.write_tenet(tenet, _auth=CONSENSUS_GUARD)
    assert len(await tmp_data.read_tenets()) == 1
    await tmp_data.reset()
    # Tenets persist across resets (collective memory preserved)
    assert len(await tmp_data.read_tenets()) == 1
