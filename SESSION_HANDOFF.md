# Session Handoff: Voting Context System

**Date:** 2026-02-22
**Status:** Phase 3 COMPLETE - Agents have historical awareness

---

## TL;DR

Agents now vote with historical context - chronicle history, personal memory, and voting records inform their decisions. **The auto-YES is gone.** Residents exercise independent judgment based on their expertise and experience.

**Next Session Prompt:**
```
Read VOTING_FIX.md for context. Phase 1-3 are complete. Continue with Phase 4: Enhance RuleBasedStrategy with richer context-aware evaluation.

Loose End: The `_record_vote_outcome()` method in agent.py exists but is never called. Wire it up in simulation.py after end_of_round() to complete the feedback loop.
```

---

## Progress Summary

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Remove auto-YES voting | DONE |
| 2 | Load real identity with specialization | DONE |
| 3 | Pass voting context to agents | DONE |
| 4 | Enhance RuleBasedStrategy | NEXT |
| 5 | Team communication (Triad deliberation) | FUTURE |
| 6 | Persistent memory across sessions | FUTURE |

---

## What Changed (Session 2 - Phase 3)

### New Models (models.py)

```python
class VoteRecord(BaseModel):
    proposal_id: str
    action: ProposalAction
    vote: bool  # True = YES, False = NO
    outcome: ProposalStatus
    round_number: int

class VotingContext(BaseModel):
    recent_events: list[ChronicleEvent]  # Last 10 chronicle events
    milestones: list[ChronicleEvent]     # Permanent milestones
    personal_memory: list[str]           # Agent's observations
    voting_history: list[VoteRecord]     # Past votes + outcomes
    squad_id: str | None
    squad_momentum: float
```

### Strategy Interface (base.py)

Added `voting_context: Optional[VotingContext] = None` to `evaluate_proposal()`

### RuleBasedStrategy (rule_based.py)

Section 8: Historical Context scoring:
- 8.1 Chronicle alignment: +0.15 if proposal matches recent events
- 8.2 Personal memory: +0.1 if matches agent's observations
- 8.3 Voting consistency: +0.1 if track record supports consolidation
- 8.4 Squad bonus: +0.05 for same-squad proposals

### LLMDrivenStrategy (llm_driven.py)

Prompts now include:
```
HISTORICAL CONTEXT:
RECENT COMMUNITY EVENTS:
- [event 1]
- [event 2]

YOUR RECENT OBSERVATIONS:
- [observation 1]

YOUR VOTING RECORD: 15 votes (12 YES), 10 successful outcomes
```

### Agent Runtime (agent.py)

- Added `chronicle` parameter to `__init__()`
- Added `_voting_history: list[VoteRecord]`
- Added `_build_voting_context()` async method
- Added `_record_vote_outcome()` method (NOT YET WIRED)
- Voting loop now passes context to strategies

### Simulation (simulation.py)

All 3 agent creation sites now pass `chronicle=self._chronicle`:
- Initial agent creation (line 234)
- `_load_evolved_agents()` (line 326)
- `_spawn_citizens()` (line 1093)

---

## Loose End: Wire Vote Outcome Recording

The feedback loop is incomplete. `_record_vote_outcome()` exists but isn't called.

**Where to wire it:** In `simulation.py._run_round()`, after `consensus.end_of_round()`:

```python
# After end_of_round resolves proposals
for proposal in self._consensus.all_proposals():
    if proposal.status != ProposalStatus.PENDING:
        for agent in self._agents:
            if agent.id in proposal.votes:
                agent._record_vote_outcome(
                    proposal.id,
                    proposal.action,
                    proposal.votes[agent.id],
                    proposal.status,
                    round_num
                )
```

---

## Critical Files

| File | What It Does |
|------|--------------|
| `VOTING_FIX.md` | Roadmap (Phases 1-6) |
| `pureswarm/models.py` | VotingContext, VoteRecord models |
| `pureswarm/agent.py` | _build_voting_context(), _record_vote_outcome() |
| `pureswarm/strategies/rule_based.py` | Section 8 historical context scoring |
| `pureswarm/strategies/llm_driven.py` | LLM prompts with HISTORICAL CONTEXT |
| `pureswarm/simulation.py` | Wires chronicle to agents |

---

## Test Status

```
tests/test_consensus.py - 5/5 PASSED
tests/test_simulation.py::test_full_simulation - PASSED
tests/test_memory.py - SKIPPED (stale import)
tests/test_messaging.py - 4 ERRORS (pre-existing)
```

---

## Verification

```bash
# Test imports
python -c "from pureswarm.models import VotingContext, VoteRecord; print('OK')"

# Run with voting context
python run_simulation.py --interactive --emergency --num_rounds 2
```

**Expected:** Dashboard shows `YES/NO` percentages - NOT 100% YES anymore.

---

## Architecture: Voting Context Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT VOTING FLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Chronicle  │    │   Personal   │    │    Voting    │  │
│  │   (events)   │    │   Memory     │    │   History    │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             ▼                               │
│                    ┌────────────────┐                       │
│                    │ VotingContext  │                       │
│                    └────────┬───────┘                       │
│                             │                               │
│         ┌───────────────────┼───────────────────┐           │
│         ▼                   ▼                   ▼           │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐    │
│  │ RuleBased  │      │ LLMDriven  │      │ (Future)   │    │
│  │ Section 8  │      │ HISTORICAL │      │            │    │
│  └─────┬──────┘      └─────┬──────┘      └────────────┘    │
│        └───────────┬───────┘                               │
│                    ▼                                        │
│           ┌────────────────┐                               │
│           │  INFORMED VOTE │                               │
│           │  (YES or NO)   │                               │
│           └────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## The Big Picture (from previous session)

- 255 agents, 908 tenets to consolidate to ~200
- Squad Warfare: Alpha/Beta/Gamma compete
- 9 LLM agents (Triad + Researchers) propose FUSE/DELETE
- 246 Residents vote with **real agency** (no more auto-YES)
- Anthropic API primary, Venice fallback

---

## Git Commits

```
642820e feat: add squad competition system with prompt economy and tenet clustering
b980c90 feat: add democracy check to dashboard - shows voting breakdown
94549c8 fix: remove auto-YES voting - residents now have real agency
[NEW]   feat: add voting context system for informed agent decisions
```

---

*"Stewardship is the root; Idolatry is the rot."*
