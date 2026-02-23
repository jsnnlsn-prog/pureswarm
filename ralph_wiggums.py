"""
Next Session Cheat Sheet (Ralph Wiggum Style)

Read VOTING_FIX.md for context. Phase 1-6 complete.

Task: Phase 7 - Redis backend for agent memory (DISTRIBUTED_ARCHITECTURE.md)

=== PHASE 6 COMPLETE ===

Individual agent memory NOW PERSISTS across sessions:
- data/agent_memories.json stores lifetime_memory and voting_history
- AgentMemoryStore class in pureswarm/memory.py
- Simulation loads memory on agent creation
- Simulation saves memory at end of each round

Structure:
{
    "agent_id_1": {
        "lifetime_memory": ["obs1", "obs2", ...],
        "voting_history": [VoteRecord, VoteRecord, ...],
        "last_active": "2024-01-01T00:00:00Z"
    },
    ...
}

=== WHAT WORKS NOW ===

- Triad votes first, residents follow
- Vote outcomes saved to agent memory (NOW PERSISTED!)
- +0.4 bonus when Triad says "approve"
- -0.3 penalty when Triad says "reject"
- Triad explains their votes (deliberation reasoning)
- Residents see why Triad voted that way
- Agents remember their past across simulation restarts

=== KEY FILES MODIFIED (Phase 6) ===

pureswarm/memory.py     - Added AgentMemoryStore class (lines 437-543)
pureswarm/agent.py      - Added initial_memory param, get_memory_snapshot()
pureswarm/simulation.py - Loads memory on agent creation, saves each round

=== NEXT PHASE: REDIS BACKEND ===

docs/archive/DISTRIBUTED_ARCHITECTURE.md line 121:
    memory:{agent_id}  HASH  Agent-specific knowledge

Redis schema already designed! Implementation path:
1. File-based done (data/agent_memories.json) [COMPLETE]
2. Redis backend (memory:{agent_id} HASH) [NEXT]

Pattern to follow:
- See RedisMemory class in memory.py for tenet storage
- AgentMemoryStore needs similar async Redis methods
- Config toggle: memory.backend = "file" | "redis"

=== GIT STATUS ===

Phase 6 changes ready to commit:
- pureswarm/memory.py (AgentMemoryStore)
- pureswarm/agent.py (initial_memory, get_memory_snapshot)
- pureswarm/simulation.py (load/save wiring)
- tests/test_memory.py (fixed imports, updated reset test)

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
