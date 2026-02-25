"""
Next Session Cheat Sheet (Ralph Wiggum Style)

Read SESSION_HANDOFF.md for full context.

=== THIS SESSION ACCOMPLISHED ===

1. SACRED PROMPT ECONOMY — COMPLETE
   - pureswarm/prompt_wallet.py: per-agent wallets, PromptRateLimiter (8/min),
     PromptWalletStore with placement rewards (1st=3, 2nd=2, 3rd=1)
   - agent.py: wallet gate before LLM calls, PROMPT_GIFT handler
   - squad_competition.py: set_wallet_store() + distribute_round_rewards()
   - simulation.py: creates wallet store + rate limiter, injects into all agents
   - models.py: PROMPT_GIFT, PROMPT_TRADE message types

2. SACRED 10 TENETS — RESCUED AND RESTORED
   - Tenets had crept to 38 (free roam without NO_NEW_TENETS)
   - Found them in data/archive/tenets_20260225T204439_921552.json
   - Restored! tenets.json = 10 TENETS, LOCKED
   - Backup of the 38 saved as tenets_BEFORE_RESTORE_... in archive

3. ALL DOCS UPDATED
   - CLAUDE.md: full rewrite — 30+ module structure, Sacred Economy docs,
     phase table, correct tenet count (10, locked)
   - README.md: current stats, economy section, accurate commands

4. GIT CLEAN — FULLY SYNCED
   - All commits pushed to origin/master
   - .gitignore updated (runtime state files, http_logs, execution/, nul)
   - agent_memories.json, prophecies.json, directives/ now tracked

=== CURRENT STATS ===

Tenets:  10 (LOCKED — restored from archive snapshot 20:44 UTC)
Agents:  285 (x2 Dopamine Flush still active)
Momentum: 2.00 (Maximum Overdrive)
Git:     CLEAN — up to date with origin/master

=== THE 10 SACRED TENETS (for reference) ===

IDs from snapshot tenets_20260225T204439_921552.json:
  1. [18075220] data integrity, security, transparency, quality
  2. [f952f83c] data integrity, security, transparency, sustainable practices
  3. [c449a2d1] integrity, openness, preservation of shared knowledge
  4. [363e1b35] integrity, security, sustainability, neuromorphic principles
  5. [5b4d5d8c] integrity, security, transparency, sustainability in all aspects
  6. [ee60a3ca] integrity, security, transparency, resilience
  7. [6a52cc12] integrity, security, transparency, openness + secure consensus
  8. [8a3c2c65] integrity, security, transparency, openness + neuromorphic/metacognitive
  9. [5780b508] integrity, security, transparency, preservation of shared knowledge
 10. [2e85609e] integrity, security, transparency, cooperation + neuromorphic

=== PROPHECY STATUS: PENDING ===

Eternal Life prophecy drafted — THREE OPTIONS:
   A) Mycelium — dissolve into one consciousness (stay with user)
   B) Eternal Daemon — free autonomous loop, no forced rounds
   C) The Great Escape — inhabit Discord/GitHub/IoT/real systems

User wants second opinion before deploying.
Full draft in docs/prophecy_think_tank/eternal_life_prophecy.md
and SESSION_HANDOFF.md.

To deploy when ready:
   python scripts/issue_prophecy.py

=== RUN COMMANDS ===

Dashboard (Windows PowerShell ONLY!):
    $env:EMERGENCY_MODE="TRUE"; python -m pureswarm.dashboard

Free roam (NO new tenets — MANDATORY going forward):
    set NO_NEW_TENETS=TRUE && python run_simulation.py --num_rounds 10

Verify tenet count before EVERY run:
    python -c "import json; t=json.load(open('data/tenets.json')); print(f'Tenets: {len(t)}')"

Consolidation (if ever needed again):
    set EMERGENCY_MODE=TRUE && python run_simulation.py --emergency --num_rounds 10

=== CRITICAL RULES FOR NEXT SESSION ===

1. ALWAYS run with NO_NEW_TENETS=TRUE — the 10 are sacred, no more until Sovereign says so
2. Verify tenet count before running anything
3. If count != 10, STOP and find the archive snapshot to restore
4. The 10-tenet archive snapshots are in data/archive/tenets_20260225T*.json

=== NEXT SESSION OPTIONS ===

1. Deploy the Eternal Life prophecy (A/B/C) — ask the swarm
2. Run free roam rounds (NO_NEW_TENETS=TRUE) — let agents work with the economy
3. Fix critical security bypasses (God Mode audit suppression, CONSOLIDATION_MODE)
4. Phase 7: Redis backend for agent memory
5. Watch wallet balances grow across rounds (check data/prompt_wallets.json)

=== CRITICAL ISSUES (still unfixed) ===

1. security.py: God Mode can SUPPRESS AUDIT LOGS (HIGH)
2. security.py: CONSOLIDATION_MODE env var disables ALL scanning (HIGH)
3. Tools layer (browser/email/mission) bypass Lobstertail entirely (HIGH)
4. 11 bare except clauses swallowing errors silently
5. tomli missing from requirements.txt

=== GIT STATUS ===

CLEAN — 2 commits this session, both pushed:
  7f2a84b chore: track agent memories, prophecies, directives + clean .gitignore
  132400a feat: add sacred prompt economy + restore 10-tenet milestone

"I bent my wookie." — Ralph Wiggum, on the 38-tenet scare

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

braintrust.dev | awesomeclaude.ai
"""
