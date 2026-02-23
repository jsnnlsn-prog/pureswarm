"""
Next Session Cheat Sheet (Ralph Wiggum Style)

Read SESSION_HANDOFF.md for full context. Phase 1-6 complete.

THE GREAT CONSOLIDATION CONTINUES!
- Started: 905 tenets
- Current: 880 tenets (25 consolidated!)
- Agents: 258 (with persistent memory!)
- Dashboard: NOW WITH LIVE PROPOSALS!

=== THIS SESSION ACCOMPLISHED ===

1. Fixed prophecy signature warnings
   - Re-signed data/.prophecy with SOVEREIGN_KEY_FALLBACK
   - No more "Invalid Prophecy Signature" spam

2. Enhanced Dashboard with NEW PANELS:
   - CONSOLIDATION TALLY: Shows 905 -> current -> 200 goal
   - VOTE TALLY: YES/NO counts, adopted/rejected/pending
   - ACTIVE PROPOSALS: Live FUSE proposals with vote counts!
   - Fixed terminal compatibility (screen=False for antigravity)

3. Added _write_round_review() to simulation.py
   - Writes proposals_detail to .round_review.json after EVERY round
   - Dashboard reads this for live proposal display

=== DASHBOARD PANELS ===

Left side (main):
- NEURAL HIVE TOPOLOGY: 258 agents visualized
- ACTIVE PROPOSALS: FUSE proposals with Y/N votes
- ACTIVE UPLINK: Audit log ticker

Right side:
- MISSION VITALS: Population, tenet count, heartbeat
- CONSOLIDATION TALLY: Progress to 200 tenets
- VOTE TALLY: YES/NO breakdown
- SQUAD ARENA: Leaderboard

=== RUN COMMANDS ===

Dashboard (Windows PowerShell - NOT antigravity terminal!):
    $env:EMERGENCY_MODE="TRUE"; python -m pureswarm.dashboard

Simulation (any terminal):
    set EMERGENCY_MODE=TRUE && python run_simulation.py --emergency --num_rounds 1

=== CURRENT STATS ===

Tenets: 880 (down from 905)
Agents: 258 with persistent memory
Round: 1 of this session (4 total consolidation rounds)
Last Vote: 1238 YES / 7 NO (99.4% approval!)
Proposals: 9 FUSE pending (one targets 44 tenets!)
Momentum: 2.00 (maximum!)

=== KNOWN ISSUES ===

1. Dashboard doesn't work in "antigravity terminal"
   - Use Windows PowerShell directly
   - Works fine there with screen=False

2. Proposals need multiple rounds to accumulate votes
   - 50% threshold required for adoption
   - Keep running rounds!

=== NEXT SESSION OPTIONS ===

1. Continue consolidation: --emergency --num_rounds 10
2. Phase 7: Redis backend for agent memory
3. Watch dashboard while running rounds!

=== KEY FILES MODIFIED ===

pureswarm/simulation.py  - Added _write_round_review() for dashboard
pureswarm/dashboard.py   - New panels: tally, votes, proposals
data/.prophecy           - Re-signed with correct key
data/.round_review.json  - Live proposal data for dashboard

=== GIT STATUS ===

4 commits ahead of origin (Phases 4-6 + dashboard fix)
+ This session's dashboard enhancements (uncommitted)

"I'm learnding!" - Ralph Wiggum, watching the dashboard

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
