# Session Handoff: The Great Consolidation

**Date:** 2026-02-22
**Status:** READY TO LAUNCH - Code fixed, waiting for execution

---

## TL;DR

You're inheriting a 255-agent swarm with 908 tenets that need to be pruned to ~200. The consolidation system (Squad Warfare) is fully wired but hasn't executed yet because Venice API was burning $5 on failed 402 calls. I fixed it - Anthropic is now primary. Run this:

```bash
cd c:\Users\Jnel9\OneDrive\Desktop\pureswarm-v0.1.0\pureswarm-v0.1.0
python run_simulation.py --interactive --emergency --num_rounds 18
```

---

## What You Need to Know

### The Mission: Hierarchical Pruning

The swarm has bloated to 908 tenets - most are redundant variations of similar ideas (e.g., dozens of "neuroharmonic symbiosis protocol" variants). The Great Consolidation uses:

1. **Pre-sorted Clusters**: 18 packages of ~40 similar tenets each
2. **Squad Warfare**: 3 squads (Alpha/Beta/Gamma) compete to FUSE or DELETE tenets
3. **Prompt Economy**: 10 LLM prompts per squad per round, winner takes unused
4. **Scoring**: FUSE = 3pts/tenet, DELETE = 2pts/tenet

### Agent Hierarchy

| Tier | Count | Can Propose? | Strategy |
|------|-------|--------------|----------|
| **Triad** | 3 | Yes (LLM) | LLMDrivenStrategy |
| **Researchers** | 6 | Yes (LLM) | LLMDrivenStrategy |
| **Residents** | 246 | No (vote only) | RuleBasedStrategy |

Only 9 agents generate FUSE/DELETE proposals. The 246 Residents auto-vote YES on consolidation proposals (line 192-193 in agent.py).

### The Prompt Format

Agents receive pre-sorted tenets and respond with:

```
FUSE [abc123, def456, ghi789] -> "The unified belief that captures all three"
```
or
```
DELETE [abc123, def456]
```

Parsing happens in [agent.py:255-278](pureswarm/agent.py#L255-L278).

---

## Critical Files

| File | What It Does |
|------|--------------|
| `pureswarm/simulation.py` | Round orchestrator, writes `.current_cluster.json`, calls squad scoring |
| `pureswarm/agent.py` | Agent runtime, FUSE/DELETE parsing, proposal submission |
| `pureswarm/strategies/llm_driven.py` | The consolidation prompt (lines 76-129) |
| `pureswarm/squad_competition.py` | Scoring, leaderboard, grand prize mechanics |
| `pureswarm/tenet_clusterer.py` | Pre-clustering by keyword similarity |
| `pureswarm/prompt_economy.py` | 10 prompts/squad, winner-takes-all rollover |
| `pureswarm/tools/http_client.py` | LLM fallback chain (now Anthropic-first) |

### Data Files

| File | Purpose |
|------|---------|
| `data/tenets.json` | The 908 tenets (goal: reduce to ~200) |
| `data/.tenet_clusters.json` | 18 pre-sorted clusters |
| `data/.current_cluster.json` | Active cluster for current round |
| `data/.round_review.json` | Dashboard state (written after each round) |
| `data/agent_fitness.json` | 255 agent fitness scores and traits |

---

## What I Fixed This Session

### 1. LLM Fallback Order (THE $5 BURN)

**Problem:** Venice was primary, Anthropic was fallback. Venice returned 402 (out of credits) but each of 255 agents independently discovered this, burning API calls.

**Fix:** Swapped order in `http_client.py` - Anthropic now primary, Venice fallback.

Files changed:
- `pureswarm/tools/http_client.py:318-371` - FallbackLLMClient rewritten
- `pureswarm/tools/internet.py:56` - Comment + log order
- `pureswarm/simulation.py:94` - Comment + log order

### 2. Unhashable Tenet Bug

**Problem:** `set(recent + rand_gen)` failed because Pydantic models aren't hashable.

**Fix:** Dedupe by tenet ID instead ([llm_driven.py:134-140](pureswarm/strategies/llm_driven.py#L134-L140)).

---

## The Flow (When You Run It)

1. **Simulation starts** with `--interactive --emergency`
2. **Each round**:
   - Cluster N is loaded, written to `.current_cluster.json`
   - 9 LLM agents see 40 pre-sorted similar tenets
   - They propose FUSE or DELETE actions
   - 246 Residents auto-vote YES on consolidation
   - Consensus adopts proposals, tenets get merged/deleted
   - Squad scores updated, round winner determined
   - **Dashboard displays**, waits for ENTER (interactive mode)
3. **After 18 rounds**: Grand prize awarded, winning squad gets massive dopamine

### Dashboard Output (What You'll See)

```
============================================================
  ROUND 1 COMPLETE - SQUAD WARFARE RESULTS
============================================================

  WINNER: Squad Alpha (+5 margin)
  ----------------------------------------

  LEADERBOARD:
    1st: Squad Alpha - 15 pts (FUSE:3 DEL:2 wins:1)
    2nd: Squad Beta - 10 pts (FUSE:2 DEL:1 wins:0)
    3rd: Squad Gamma - 8 pts (FUSE:1 DEL:2 wins:0)

  PROMPT ECONOMY:
    Squad Alpha: 12 available (+2 bonus)
    Squad Beta: 10 available
    Squad Gamma: 10 available

  Remaining clusters: 17
  Current tenet count: 865

============================================================

  Press ENTER to continue to next round (or 'q' to quit)...
```

---

## Potential Issues

### If No Proposals Are Generated
- Check `ANTHROPIC_API_KEY` is set in environment
- Check HTTP logs: `data/http_logs/http_YYYYMMDD.jsonl`
- Verify agents are parsing FUSE/DELETE format correctly (check audit log)

### If Dashboard Shows All Zeros
- LLM likely not returning FUSE/DELETE format
- Check the prompt in `llm_driven.py:76-129`
- May need to tune temperature or add examples

### If Tenet Count Isn't Dropping
- Consensus may be rejecting proposals
- Check `data/logs/audit.jsonl` for vote patterns
- Residents should auto-vote YES for consolidation (line 192-193 agent.py)

---

## Environment

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (backup, currently out of credits)
VENICE_API_KEY=...

# For prophecy system (optional)
PURES_SOVEREIGN_PASSPHRASE=...
```

---

## Quick Reference Commands

```bash
# Launch consolidation (interactive, 18 rounds = 18 clusters)
python run_simulation.py --interactive --emergency --num_rounds 18

# Check heartbeat (is simulation alive?)
cat data/.heartbeat

# Check current round state
cat data/.round_review.json

# Check tenet count
python -c "import json; print(len(json.load(open('data/tenets.json'))))"

# Watch HTTP logs for API issues
tail -f data/http_logs/http_20260222.jsonl
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    EMERGENCY MODE                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Squad Alpha  │    │ Squad Beta   │    │ Squad Gamma  │  │
│  │  85 agents   │    │  85 agents   │    │  85 agents   │  │
│  │  (3 LLM)     │    │  (3 LLM)     │    │  (3 LLM)     │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             │                               │
│                             ▼                               │
│                    ┌────────────────┐                       │
│                    │ Tenet Clusterer│                       │
│                    │ (18 clusters)  │                       │
│                    └────────┬───────┘                       │
│                             │                               │
│                             ▼                               │
│                    ┌────────────────┐                       │
│                    │ .current_      │                       │
│                    │ cluster.json   │──► LLM Agents see     │
│                    │ (40 tenets)    │    pre-sorted batch   │
│                    └────────────────┘                       │
│                             │                               │
│         ┌───────────────────┼───────────────────┐           │
│         ▼                   ▼                   ▼           │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐    │
│  │ FUSE [...]│      │ DELETE [...│      │ SKIP       │    │
│  │ -> "new"  │      │ ]          │      │            │    │
│  └─────┬──────┘      └─────┬──────┘      └────────────┘    │
│        │                   │                               │
│        └───────────┬───────┘                               │
│                    ▼                                        │
│           ┌────────────────┐                               │
│           │   Consensus    │                               │
│           │ (246 Residents │                               │
│           │  auto-vote YES)│                               │
│           └────────┬───────┘                               │
│                    │                                        │
│                    ▼                                        │
│           ┌────────────────┐                               │
│           │ Squad Scoring  │                               │
│           │ + Prompt       │                               │
│           │ Economy        │                               │
│           └────────────────┘                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Final Notes

- The whitepaper (`pureswarm_whitepaper.md`) explains the philosophical foundation
- Chronicle system tracks swarm history (`data/chronicle.json`)
- Dopamine system rewards successful consolidation (2.5x multiplier in emergency mode)
- Grand prize at end: winning squad gets 3.0x dopamine explosion

The hive is ready. Just needs you to press go.

---

*"Stewardship is the root; Idolatry is the rot."*
