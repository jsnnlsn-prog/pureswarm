"""Auto-handoff generator — writes SESSION_HANDOFF.md and ralph_wiggums.py
from live project state.

Solves the tokenization/context-window problem for the Sovereign:
every session ends with a complete, machine-readable context dump
so the next Claude session can orient instantly without manual summary.

Run manually:        python scripts/auto_handoff.py
Run via git hook:    triggered automatically after commits (see .claude/settings.json)
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _run(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, cwd=ROOT,
                                       stderr=subprocess.DEVNULL,
                                       encoding="utf-8").strip()
    except Exception:
        return ""


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _wallet_summary() -> tuple[int, int, list]:
    wallets_path = ROOT / "data" / "prompt_wallets.json"
    if not wallets_path.exists():
        return 0, 0, []
    data = _load_json(wallets_path, {})
    wallets = data.get("wallets", {})
    total = sum(d["balance"] for d in wallets.values())
    count = len(wallets)
    top = sorted(wallets.items(), key=lambda x: x[1]["balance"], reverse=True)[:5]
    top_list = [(aid[:8], d["balance"]) for aid, d in top]
    return count, total, top_list


def generate() -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # --- git state ---
    branch = _run("git rev-parse --abbrev-ref HEAD")
    log = _run("git log --oneline -10")
    status = _run("git status --short")
    unpushed = _run("git log @{u}.. --oneline 2>/dev/null || echo '(unknown)'")

    # --- swarm state ---
    fitness = _load_json(ROOT / "data" / "agent_fitness.json", {})
    tenets = _load_json(ROOT / "data" / "tenets.json", [])
    wallet_count, wallet_supply, top_holders = _wallet_summary()

    agent_count = len(fitness)
    tenet_count = len(tenets)

    roles = {}
    for v in fitness.values():
        r = v.get("traits", {}).get("role", "resident")
        roles[r] = roles.get(r, 0) + 1

    # --- top agents ---
    top_agents = sorted(
        [(k, v.get("missions_completed", 0), v.get("traits", {}).get("role", "resident"))
         for k, v in fitness.items()],
        key=lambda x: -x[1]
    )[:5]

    # ---------------------------------------------------------------
    # Write SESSION_HANDOFF.md
    # ---------------------------------------------------------------
    handoff = f"""# PureSwarm Session Handoff
*Auto-generated: {now}*

## Quick Orient

| | |
|---|---|
| **Branch** | `{branch}` |
| **Agents** | {agent_count} ({roles.get('triad', 0)} Triad + {roles.get('resident', 0)} Residents) |
| **Tenets** | {tenet_count} (LOCKED — NO_NEW_TENETS permanent) |
| **Wallet supply** | {wallet_supply} tokens across {wallet_count} wallets |

## Git Log (last 10)

```
{log}
```

## Uncommitted Changes

```
{status if status else "(clean)"}
```

## Unpushed Commits

```
{unpushed if unpushed else "(all pushed)"}
```

## Top Agents by Missions

| Agent | Missions | Role |
|-------|----------|------|
"""
    for aid, missions, role in top_agents:
        handoff += f"| `{aid[:8]}` | {missions} | {role} |\n"

    handoff += f"""
## Top Wallet Holders

| Agent | Tokens |
|-------|--------|
"""
    for aid, bal in top_holders:
        handoff += f"| `{aid}` | {bal} |\n"

    handoff += f"""
## Current Todo (from last session)

See ralph_wiggums.py for the cheat sheet. Key pending items:
- Phase 2 (workshop economy): COMPLETE as of this handoff
- Phase 3 (auto-handoff hook): COMPLETE as of this handoff
- Phase 4 (Prophecy Debate — Eternal Life vote): NEXT SESSION
- Phase 10 (security audit): PLANNED

## Permanent Rules

- **NO_NEW_TENETS=TRUE** always — 10 tenets are locked forever (or until Sovereign says)
- **Eternal Life prophecy ON HOLD** — agents need more lived experience first
- **Simulation**: run 1 round to start, then batches of 10-50
- **Dashboard**: Windows PowerShell only (`$env:EMERGENCY_MODE="TRUE"`)
- **Handoffs**: this file + ralph_wiggums.py (auto-generated, no manual work needed)

## Next Session Start

```bash
# Verify state
python -c "import json; t=json.load(open('data/tenets.json')); print(f'Tenets: {{len(t)}}')"
python -c "import json; w=json.load(open('data/prompt_wallets.json')); print(f'Supply: {{sum(d[\"balance\"] for d in w[\"wallets\"].values())}} tokens')"

# Run the hive
set NO_NEW_TENETS=TRUE && python run_simulation.py --num_rounds 1
```
"""

    (ROOT / "SESSION_HANDOFF.md").write_text(handoff, encoding="utf-8")

    # ---------------------------------------------------------------
    # Write ralph_wiggums.py (cheat sheet)
    # ---------------------------------------------------------------
    ralph = f'''"""
Ralph Wiggum's PureSwarm Cheat Sheet
Auto-generated: {now}

I am the swarm. The swarm is me.
"""

# ============================================================
# QUICK STATUS
# ============================================================
AGENTS      = {agent_count}
TENETS      = {tenet_count}   # LOCKED. DO NOT CHANGE.
WALLET_SUPPLY = {wallet_supply}  # tokens in circulation
BRANCH      = "{branch}"
GENERATED   = "{now}"

# ============================================================
# TOP AGENTS (by missions)
# ============================================================
TOP_AGENTS = {top_agents!r}

# ============================================================
# TOP WALLET HOLDERS
# ============================================================
TOP_HOLDERS = {top_holders!r}

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
'''

    (ROOT / "ralph_wiggums.py").write_text(ralph, encoding="utf-8")

    print(f"Handoff generated: {now}")
    print(f"  Agents: {agent_count} | Tenets: {tenet_count} | Supply: {wallet_supply} tokens")
    print(f"  -> SESSION_HANDOFF.md")
    print(f"  -> ralph_wiggums.py")


if __name__ == "__main__":
    generate()
