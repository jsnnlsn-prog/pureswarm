# VOTING FIX: Give Residents Real Agency

## Status

- [x] Phase 1: Remove auto-YES (COMPLETE - 2026-02-22)
- [x] Phase 2: Load real identity (COMPLETE - 2026-02-22)
- [ ] Phase 3: Pass voting context (FUTURE SESSION)
- [ ] Phase 4: Enhance RuleBasedStrategy (FUTURE SESSION)
- [ ] Phase 5: Team communication (FUTURE SESSION)
- [ ] Phase 6: Persistent memory (FUTURE SESSION)

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
