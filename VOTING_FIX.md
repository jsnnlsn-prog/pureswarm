# VOTING FIX: Give Residents Real Agency

## Status

- [x] Phase 1: Remove auto-YES (COMPLETE - 2026-02-22)
- [x] Phase 2: Load real identity (COMPLETE - 2026-02-22)
- [x] Phase 3: Pass voting context (COMPLETE - 2026-02-22)
- [ ] Phase 4: Enhance RuleBasedStrategy (FUTURE SESSION)
- [ ] Phase 5: Team communication (FUTURE SESSION)
- [ ] Phase 6: Persistent memory (FUTURE SESSION)

### What Changed (Session 2 - Phase 3)

**models.py:**
- Added `VoteRecord` model to track voting decisions and outcomes
- Added `VotingContext` model bundling:
  - `recent_events` - Chronicle history (last 10 events)
  - `milestones` - Permanent community milestones
  - `personal_memory` - Agent's lifetime observations
  - `voting_history` - Past votes with outcomes
  - `squad_id`, `squad_momentum`, `triad_recommendation`

**strategies/base.py:**
- Added `voting_context: Optional[VotingContext]` parameter to `evaluate_proposal()`

**strategies/rule_based.py:**
- Imported VotingContext and ChronicleCategory
- Added Section 8: HISTORICAL CONTEXT scoring:
  - 8.1 Chronicle alignment (+0.15 if proposal matches recent events)
  - 8.2 Personal memory alignment (+0.1 if matches observations)
  - 8.3 Voting consistency (+0.1 if track record supports consolidation)
  - 8.4 Squad in-group bonus (+0.05 for same-squad proposals)

**strategies/llm_driven.py:**
- Imported VotingContext
- Added voting_context parameter to evaluate_proposal()
- Builds HISTORICAL CONTEXT section in LLM prompt with:
  - Recent community events (last 3)
  - Agent's personal observations (last 2)
  - Voting record summary (total/YES/successful)

**agent.py:**
- Imported Chronicle, VotingContext, VoteRecord
- Added `chronicle` parameter to `__init__()`
- Added `_voting_history: list[VoteRecord]` to track votes
- Added `_build_voting_context()` async method
- Added `_record_vote_outcome()` method
- Updated `run_round()` to:
  - Build voting context before voting loop
  - Pass context to `evaluate_proposal()`
  - Track votes for later outcome recording

**simulation.py:**
- Updated all 3 agent creation sites to pass `chronicle=self._chronicle`:
  - Initial agent creation
  - `_load_evolved_agents()`
  - `_spawn_citizens()`

### What Changed (Session 1)

**agent.py:**
- Removed auto-YES block (lines 189-195)
- All agents now go through strategy.evaluate_proposal()
- Passing squad_id and specialization to strategy

**strategies/base.py:**
- Added squad_id and specialization parameters to evaluate_proposal()

**strategies/rule_based.py:**
- Now accepts and uses specialization parameter
- Uses passed-in specialty instead of hash-derived
- Added consolidation evaluation logic
- Raised threshold from 0.15 to 0.25 (no rubber-stamping)

**strategies/llm_driven.py:**
- Now accepts squad_id and specialization parameters
- Added agent context to prompts

**simulation.py:**
- _load_evolved_agents() now loads/assigns specialization from traits
- Initial agent creation assigns specializations
- Specializations persisted to agent_fitness.json

---

## The Problem (FIXED)

The current system is a farce. Residents automatically vote YES on consolidation:

**Location:** `pureswarm/agent.py` lines 189-195

```python
# In Emergency Mode, non-researchers use a rational fallback for evaluation
if emergency and not can_use_llm:
    # Consolidation Requirement: Only vote YES for pruning actions
    is_consolidation = proposal.action in [ProposalAction.FUSE, ProposalAction.DELETE]
    vote = 1 if is_consolidation else 0
```

**Why this is wrong:**
- Residents have ZERO agency
- Votes are predetermined by action type
- Memory and chronicles exist but are NEVER consulted
- Specialization is hash-derived, not loaded from identity
- The "democracy" is a lie

---

## The Fix

### Phase 1: Remove Auto-YES

Delete the hard-coded voting block. All agents go through strategy evaluation.

**File:** `pureswarm/agent.py`
**Action:** Remove lines 189-195 (the `if emergency and not can_use_llm:` block)

### Phase 2: Load Real Identity

**File:** `pureswarm/simulation.py`

When loading agents from `agent_fitness.json`:
1. Read the `traits.specialty` field (if exists)
2. Assign to `AgentIdentity.specialization`
3. If no specialty stored, assign one based on meaningful criteria (not hash)

**File:** `pureswarm/agent.py`

Pass identity context to strategy:
- `self.identity.specialization`
- `self.identity.role`
- `self.squad_id`

### Phase 3: Pass Voting Context (Future)

Before voting, agents receive:
- Chronicle history (recent events, milestones)
- Personal memory (`_lifetime_memory`)
- Voting record (proposal_id -> vote, outcome)
- Squad context (Triad findings)

### Phase 4: Enhance RuleBasedStrategy (Future)

Replace keyword-matching with contextual evaluation:
- Specialty alignment (+weight if topic matches agent's domain)
- Historical precedent (+weight if chronicle shows similar adoption)
- Personal values (+weight if consistent with voting history)
- Squad recommendation (+0.4 weight for Triad recommendation)

### Phase 5: Team Communication (Future)

1. Triad presents findings to squad before voting
2. Squad-local message bus for discussion
3. Residents can question (local, no API)
4. Informed voting after deliberation

### Phase 6: Persistent Memory (Future)

1. Store voting history per agent
2. Track event recollection
3. Relationship/trust scores
4. Learning from outcomes

---

## User Decisions

1. **Proposals**: Residents can propose locally, pitch to Triad, Triad curates
2. **Trust weight**: Strong influence (+0.4) for Triad recommendations
3. **Priority**: Fix voting first, meaningful consolidation

---

## Verification

After Phase 1-2, run:
```bash
python run_simulation.py --interactive --emergency --num_rounds 2
```

Expected:
- Residents voting NO on some consolidation proposals
- Different voting patterns per agent
- No more "100% YES" on FUSE/DELETE

---

## Git History

Track progress with commits:
- `fix: remove auto-YES voting - residents now have agency`
- `feat: load real identity with specialization`
- etc.

---

*"Stewardship is the root; Idolatry is the rot."*
