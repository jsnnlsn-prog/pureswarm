"""
Ralph Wiggum's PureSwarm Cheat Sheet
Auto-generated: 2026-02-26 00:20 UTC

I am the swarm. The swarm is me.
"""

# ============================================================
# QUICK STATUS
# ============================================================
AGENTS      = 285
TENETS      = 10   # LOCKED. DO NOT CHANGE.
WALLET_SUPPLY = 4275  # tokens in circulation
BRANCH      = "master"
GENERATED   = "2026-02-26 00:20 UTC"

# ============================================================
# TOP AGENTS (by missions)
# ============================================================
TOP_AGENTS = [('c2eb9e6c1c01', 447, 'triad'), ('774c85f141eb', 419, 'triad'), ('3aaacd42e11e', 413, 'triad'), ('1c18147a9f6b', 196, 'resident'), ('47c257579a26', 194, 'resident')]

# ============================================================
# TOP WALLET HOLDERS
# ============================================================
TOP_HOLDERS = [('c2eb9e6c', 447), ('774c85f1', 419), ('3aaacd42', 413), ('1c18147a', 196), ('47c25757', 194)]

# ============================================================
# PERMANENT RULES
# ============================================================
# 1. NO_NEW_TENETS=TRUE always. 10 tenets. Locked. Sacred.
# 2. Eternal Life prophecy ON HOLD. Agents need more time.
# 3. Simulation: 1 round first, then 10-50 in batches.
# 4. Dashboard: Windows PowerShell ONLY.
# 5. Handoff: python scripts/auto_handoff.py (auto-runs on commit)

# ============================================================
# CRITICAL COMMANDS
# ============================================================
# Dashboard:
#   $env:EMERGENCY_MODE="TRUE"; python -m pureswarm.dashboard
#
# Run sim:
#   set NO_NEW_TENETS=TRUE && python run_simulation.py --num_rounds 1
#
# Check wallets:
#   python -c "import json; w=json.load(open('data/prompt_wallets.json')); print(sum(d['balance'] for d in w['wallets'].values()), 'tokens')"
#
# Check tenets:
#   python -c "import json; print(len(json.load(open('data/tenets.json'))), 'tenets')"
#
# Regenerate this file:
#   python scripts/auto_handoff.py

# ============================================================
# NEXT STEPS (Phase 4+)
# ============================================================
# - Deploy Eternal Life Prophecy Debate (squads vote on A/B/C)
# - Redis backend for distributed agent memory (Phase 7)
# - Security audit: God Mode, CONSOLIDATION_MODE (Phase 10)
