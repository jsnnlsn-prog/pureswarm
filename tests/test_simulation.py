"""Integration test — run a short simulation and verify emergence."""

import asyncio
import pytest
from pathlib import Path
from pureswarm.simulation import Simulation


@pytest.mark.asyncio
async def test_full_simulation(tmp_path):
    sim = Simulation(
        num_agents=4,
        num_rounds=10,
        seed_prompt="Seek collective purpose through interaction and preservation of context",
        data_dir=tmp_path,
    )
    report = await sim.run()

    # Basic sanity checks
    assert report.num_agents == 4
    assert report.num_rounds == 10
    assert len(report.rounds) == 10
    assert report.finished_at is not None

    # Emergence: at least some tenets should have been adopted
    assert len(report.final_tenets) > 0, "No tenets emerged — agents failed to converge"

    # Verify convergence trend: later rounds should have more total tenets
    first_half_max = max(r.total_tenets for r in report.rounds[:5])
    second_half_max = max(r.total_tenets for r in report.rounds[5:])
    assert second_half_max >= first_half_max, "No growth in tenets over time"

    # Verify audit trail exists
    audit_file = tmp_path / "logs" / "audit.jsonl"
    assert audit_file.exists()
    lines = audit_file.read_text().strip().split("\n")
    assert len(lines) > 0, "Audit log is empty"


@pytest.mark.asyncio
async def test_single_agent_no_crash(tmp_path):
    """Edge case: a single agent can't vote on its own proposals."""
    sim = Simulation(num_agents=1, num_rounds=5, data_dir=tmp_path)
    report = await sim.run()
    assert len(report.rounds) == 5
    # Single agent proposals can never get votes, so no tenets expected
    assert len(report.final_tenets) == 0


@pytest.mark.asyncio
async def test_large_swarm(tmp_path):
    """Verify the system handles more agents gracefully."""
    sim = Simulation(num_agents=10, num_rounds=5, data_dir=tmp_path)
    report = await sim.run()
    assert len(report.rounds) == 5
    assert report.num_agents == 10
