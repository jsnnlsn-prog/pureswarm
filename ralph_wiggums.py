"""
Next Session Cheat Sheet (Ralph Wiggum Style)

Read VOTING_FIX.md for context. Phase 1-5 complete.

Task: Phase 6 - Persistent memory across sessions

=== THE PROBLEM ===

Individual agent memory is LOST when simulation ends:
- _lifetime_memory: list[str]  (observations like "Round 5: Proposal blocked")
- _voting_history: list[VoteRecord]  (past votes + outcomes)

Shared memory ALREADY persists:
- data/tenets.json (SharedMemory - consensus-gated)
- data/chronicle.json (Chronicle - community history)
- data/agent_fitness.json (FitnessTracker - traits, successes)

=== THE SOLUTION ===

Option B recommended: Single file data/agent_memories.json

Structure:
{
    "agent_id_1": {
        "lifetime_memory": ["obs1", "obs2", ...],
        "voting_history": [VoteRecord, VoteRecord, ...]
    },
    ...
}

=== KEY FILES ===

pureswarm/memory.py        - SharedMemory + RedisMemory backends (reference pattern)
pureswarm/agent.py         - Add save/load methods for _lifetime_memory, _voting_history
pureswarm/simulation.py    - Wire save on round end, load on agent creation
pureswarm/evolution.py     - FitnessTracker pattern (already saves to JSON)

=== DISTRIBUTED ARCHITECTURE ===

docs/archive/DISTRIBUTED_ARCHITECTURE.md line 121:
    memory:{agent_id}  HASH  Agent-specific knowledge

Redis schema already designed! Implementation path:
1. File-based first (data/agent_memories.json)
2. Redis backend later (memory:{agent_id} HASH)

=== WHAT WORKS NOW ===

- Triad votes first, residents follow
- Vote outcomes saved to agent memory (in-memory only!)
- +0.4 bonus when Triad says "approve"
- -0.3 penalty when Triad says "reject"
- Triad explains their votes (deliberation reasoning)
- Residents see why Triad voted that way

=== PHASE 5 CHANGES (just completed) ===

- strategies/base.py: evaluate_proposal returns (vote, reasoning) tuple
- strategies/llm_driven.py: Parses LLM response for reasoning after YES/NO
- agent.py: Stores deliberation in _deliberation_reasoning dict
- simulation.py: Publishes deliberations to .squad_deliberations.json
- models.py: VotingContext has triad_deliberations field

=== GIT STATUS ===

Uncommitted changes from Phase 5 implementation.
Run: git status to see what needs committing.

"I'm helping!" - Ralph Wiggum, signing off.

---

Overview of the Ralph Wiggum Method

The Ralph Wiggum method is an innovative approach to software development
using large language models (LLMs). Named after a character from The Simpsons,
this technique emphasizes persistent iteration and learning from failures.

Key Principles:
- Iteration Over Perfection: Continuous improvement over first-try perfection
- Autonomous Loop: Simple Bash loop feeding prompts to AI until done
- Context Management: Progress in files and git history

The Loop Structure:
    while :; do cat PROMPT.md | agent; done

Phases:
1. Define Requirements
2. Execute the Loop
3. Learn and Retry

Benefits:
- Cost Efficiency
- Unattended Operation
- Flexibility

braintrust.dev | awesomeclaude.ai
"""
