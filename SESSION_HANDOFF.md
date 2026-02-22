# Session Handoff: Triad Recommendation System

**Date:** 2026-02-22
**Status:** Phase 4 COMPLETE - Triad leadership guides resident voting

---

## TL;DR

Agents vote with full context: chronicle history, personal memory, voting records, AND Triad recommendations. **The feedback loop is complete.** Triad members vote first, their recommendations are published, and Residents receive +0.4 weight guidance from their squad's Triad.

**Next Session Prompt:**
```
Read VOTING_FIX.md for context. Phase 1-4 are complete. Continue with Phase 5: Team communication (Triad deliberation before voting).

Key features working:
- Vote outcomes recorded to agent history (feedback loop)
- Triad votes first, publishes recommendations to .triad_recommendations.json
- Residents read per-proposal recommendations for their squad
- +0.4 weight for Triad "approve", -0.3 for "reject"
```

---

## Progress Summary

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Remove auto-YES voting | DONE |
| 2 | Load real identity with specialization | DONE |
| 3 | Pass voting context to agents | DONE |
| 4 | Triad recommendation system (+0.4 weight) | DONE |
| 5 | Team communication (Triad deliberation) | NEXT |
| 6 | Persistent memory across sessions | FUTURE |

---

## What Changed (Session 3 - Phase 4)

### Feedback Loop Complete (simulation.py)

After `end_of_round()`, vote outcomes are now recorded:

```python
for proposal in self._consensus.all_proposals():
    if proposal.status != ProposalStatus.PENDING:
        for agent in self._agents:
            if agent.id in proposal.votes:
                agent._record_vote_outcome(...)
```

### Triad Deliberation First (simulation.py)

Agents now run in two phases:
1. Triad/Researchers vote first (parallel among themselves)
2. `_publish_triad_recommendations()` writes votes to `.triad_recommendations.json`
3. Residents vote second (read Triad guidance)

### Per-Proposal Recommendations (models.py, agent.py)

- Changed `triad_recommendation: str` to `triad_recommendations: dict[str, str]`
- Maps `proposal_id -> "approve"/"reject"` for accurate per-proposal guidance

### Triad Influence (rule_based.py)

Section 8.5 added:
- +0.4 weight when Triad recommends "approve"
- -0.3 weight when Triad recommends "reject"

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
