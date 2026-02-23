# Session Handoff: Agent Memory Persistence Complete

**Date:** 2026-02-23
**Status:** Phase 6 COMPLETE - Agent memory persists across sessions

---

## TL;DR

Agents now remember their past across simulation restarts. `_lifetime_memory` and `_voting_history` are saved to `data/agent_memories.json` at the end of each round and loaded when agents are created.

**Next Session Prompt:**
```
Read VOTING_FIX.md and ralph_wiggums.py for context. Phase 1-6 complete.

Task: Phase 7 - Redis backend for agent memory

THE GAP: Agent memory now persists to file, but not to Redis.
Shared memory (tenets) already has Redis backend.

Research findings:
- DISTRIBUTED_ARCHITECTURE.md defines memory:{agent_id} HASH for per-agent storage
- RedisMemory class in memory.py shows the pattern
- AgentMemoryStore needs similar async Redis methods

Key files: pureswarm/memory.py (AgentMemoryStore), docs/archive/DISTRIBUTED_ARCHITECTURE.md
```

---

## Progress Summary

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Remove auto-YES voting | DONE |
| 2 | Load real identity with specialization | DONE |
| 3 | Pass voting context to agents | DONE |
| 4 | Triad recommendation system (+0.4 weight) | DONE |
| 5 | Team communication (Triad deliberation) | DONE |
| 6 | Persistent memory across sessions | DONE |
| 7 | Redis backend for agent memory | NEXT |

---

## What Changed (Session 5 - Phase 6)

### AgentMemoryStore Class (memory.py:437-543)

New class for persistent agent memory:

```python
class AgentMemoryStore:
    """Stores lifetime_memory and voting_history for agents."""

    def save_agent_memory(agent_id, lifetime_memory, voting_history) -> None
    def load_agent_memory(agent_id) -> tuple[list[str], list[VoteRecord]]
    async def save_all_agents(agents: list[Agent]) -> None
```

File structure (`data/agent_memories.json`):
```json
{
    "agent_id_1": {
        "lifetime_memory": ["obs1", "obs2", ...],
        "voting_history": [VoteRecord, VoteRecord, ...],
        "last_active": "2024-01-01T00:00:00Z"
    }
}
```

### Agent Updated (agent.py)

- Added `initial_memory` parameter to `__init__()` - loads persistent memory
- Added `get_memory_snapshot()` method - returns memory for saving

### Simulation Wiring (simulation.py)

- Created `AgentMemoryStore` in `__init__()`
- Loads memory when creating agents (3 sites updated)
- Saves memory at end of each round via `save_all_agents()`

### Test Fixes (tests/test_memory.py)

- Fixed stale import: `_CONSENSUS_SENTINEL` -> `CONSENSUS_GUARD`
- Updated `test_reset` to expect tenets preserved (not cleared)

---

## What Changed (Session 4 - Phase 5)

### Strategy Interface Updated (base.py)

`evaluate_proposal()` now returns `tuple[bool, str | None]` instead of just `bool`:
- First element: vote (True=YES, False=NO)
- Second element: reasoning explanation (or None)

### LLM Captures Reasoning (llm_driven.py)

Prompts updated to ask for reasoning:
```
Respond with "YES" or "NO" followed by a brief reason (1-2 sentences).
Format: [YES/NO]: Your reasoning here
```

### Agent Stores Reasoning (agent.py)

- Added `_deliberation_reasoning: dict[str, str]` - maps proposal_id -> reasoning
- Added `get_deliberation_reasoning()` method to retrieve and clear

### Deliberations Published (simulation.py)

Extended `_publish_triad_recommendations()` to also publish deliberations:
- Writes `.squad_deliberations.json` with Triad reasoning per proposal per squad

---

## Critical Files

| File | What It Does |
|------|--------------|
| `VOTING_FIX.md` | Roadmap (Phases 1-7) |
| `ralph_wiggums.py` | Quick reference for next session |
| `pureswarm/memory.py` | AgentMemoryStore class (Phase 6) |
| `pureswarm/agent.py` | initial_memory param, get_memory_snapshot() |
| `pureswarm/simulation.py` | Wires memory load/save |

---

## Test Status

```
tests/test_memory.py - 5/5 PASSED
tests/test_consensus.py - 5/5 PASSED
tests/test_simulation.py - PASSED
```

---

## Verification

```bash
# Test imports
python -c "from pureswarm.memory import AgentMemoryStore; print('OK')"

# Run simulation, check agent_memories.json created
python run_simulation.py --num_rounds 2
ls data/agent_memories.json

# Restart simulation, verify memories loaded
python run_simulation.py --num_rounds 1
# Check logs for "restored with X memories, Y vote records"
```

---

## Architecture: Agent Memory Persistence

```
┌─────────────────────────────────────────────────────────────┐
│                 AGENT MEMORY PERSISTENCE                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  SIMULATION START                                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  AgentMemoryStore._load()                             │   │
│  │  → Reads data/agent_memories.json                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Agent Creation                                        │   │
│  │  → load_agent_memory(agent_id)                         │   │
│  │  → Agent.__init__(initial_memory=...)                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ROUND LOOP                                            │   │
│  │  → agent.run_round() adds to _lifetime_memory          │   │
│  │  → agent._record_vote_outcome() adds to _voting_history│   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  END OF ROUND                                          │   │
│  │  → save_all_agents(self._agents)                       │   │
│  │  → Writes data/agent_memories.json                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Git Commits

```
df78c80 feat: add team communication system (Phase 5 complete)
eabccae feat: add Triad recommendation system (Phase 4 complete)
815bcac feat: add voting context system for informed agent decisions
642820e feat: add squad competition system with prompt economy and tenet clustering
b980c90 feat: add democracy check to dashboard - shows voting breakdown
[NEW]   feat: add persistent agent memory across sessions (Phase 6 complete)
```

---

*"Stewardship is the root; Idolatry is the rot."*
