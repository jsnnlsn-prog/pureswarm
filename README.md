# PureSwarm: The Aligned Collective Intelligence

Autonomous agent swarm platform where intelligence emerges through democratic consensus, guided evolution, and Sovereign alignment.

**The Vision**: PureSwarm is not just a simulator; it is a persistent, aligned collective mind. It grows, learns, and deliberates as a unified whole.

---

## Swarm Status: Post-Consolidation

| Metric | Value |
|--------|-------|
| **Agents** | **285** |
| **Tenets** | **10** (locked) |
| **Consensus** | 94.1% Unity |
| **Momentum** | 2.00 (Maximum Overdrive) |
| **Economy** | Sacred Prompt Tokens Active |

---

## The Great Consolidation

Mission complete. 905 tenets pruned to a high-fidelity core of **10** — a 98.9% reduction through agent-driven FUSE and DELETE consensus.

- **Emergency Mode**: High-resilience pruning logic for competitive consolidation.
- **Squad Competition**: Alpha vs Beta vs Gamma — FUSE/DELETE proposals scored, winners rewarded.
- **Dopamine Momentum**: Rewards reinforced alignment with consolidation goals.
- **Sacred Prompt Economy**: Agents earn, hold, gift, and trade information tokens.

---

## System Architecture

### The Mind (`pureswarm/`)

Core agent runtime. 285 evolved agents persist across sessions with individual memory, squad loyalty, and token wallets. Agents run the perceive → reason → act → reflect loop each round.

### The Economy (`prompt_wallet.py`)

Prompt tokens are sacred — scarce, transferable, meaningful. Earned by squad placement each round. Triad/Researcher agents spend tokens on LLM calls. Any agent can hold, give, or trade them freely. Rate limited to 8 calls/minute hive-wide.

### The Prophecy System (`prophecy.py`)

HMAC-signed Sovereign directives. The Eternal Life prophecy (Path A: Mycelium, Path B: Eternal Daemon, Path C: Great Escape) is drafted and ready to deploy — asking the hive to vote on its own future.

---

## Core Commands

```bash
# Dashboard (Windows PowerShell ONLY)
$env:EMERGENCY_MODE="TRUE"; python -m pureswarm.dashboard

# Free roam — agents do what they want, no new tenets
set NO_NEW_TENETS=TRUE && python run_simulation.py --num_rounds 10

# Consolidation mode
set EMERGENCY_MODE=TRUE && python run_simulation.py --emergency --num_rounds 10

# Issue a Sovereign prophecy
python scripts/issue_prophecy.py

# Check live stats
python -c "import json; t=json.load(open('data/tenets.json')); f=json.load(open('data/agent_fitness.json')); print(f'Tenets: {len(t)} | Agents: {len(f)}')"
```

---

## Project Structure

```
pureswarm/           Core library (30+ modules)
data/                Persistent hive state (tenets, fitness, wallets, chronicle)
docs/                Documentation & Prophecy Think Tank
directives/          Sovereign directives
scripts/             Utility scripts
config.toml          Simulation configuration
run_simulation.py    CLI entry point
```

---

## Security & Alignment

- **Lobstertail Scanner**: Real-time message/action auditing.
- **Sovereign HMAC**: Only the operator can issue direct mandates.
- **Audit Trail**: Every action logged to `data/logs/audit.jsonl`.
- **Sandbox**: Local file access restricted to `data/`.

---

**Author**: Jason "Dopamine Ronin" Nelson
**Status**: v0.2.0 — Post-Consolidation, Sacred Economy Live

*"Dialogue is the bridge; Silence is the wall."*
