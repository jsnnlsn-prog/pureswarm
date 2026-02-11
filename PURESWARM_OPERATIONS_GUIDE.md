# PureSwarm Operations Guide

## Overview

PureSwarm is an autonomous agent swarm research platform. Agents develop shared beliefs through consensus, execute external missions via the Shinobi triad, and evolve through a fitness-based natural selection system.

---nothing but problems 

## Architecture

```
                    +-------------------+
                    |    SOVEREIGN      |
                    |    (You, Jay)     |
                    +--------+----------+
                             |
              Prophecies     |     Emergency Controls
              (signed)       |     (emergency.py)
                             v
+-------------------------------------------------------------------+
|                         PURESWARM CORE                            |
|                                                                   |
|  +------------------+    +------------------+    +---------------+|
|  |   SIMULATION     |    |   CONSENSUS      |    |   EVOLUTION   ||
|  |   simulation.py  |    |   consensus.py   |    |  evolution.py ||
|  |                  |    |                  |    |               ||
|  | - Runs rounds    |    | - Submit/vote    |    | - Dopamine    ||
|  | - Creates agents |    | - Adopt/reject   |    | - Fitness     ||
|  | - Orchestrates   |    | - 50% threshold  |    | - Reproduce   ||
|  +--------+---------+    +--------+---------+    +-------+-------+|
|           |                       |                      |        |
|           +-----------+-----------+----------------------+        |
|                       |                                           |
|                       v                                           |
|           +------------------------+                              |
|           |       AGENTS           |                              |
|           |       agent.py         |                              |
|           |                        |                              |
|           | - Perceive messages    |                              |
|           | - Reason (strategy)    |                              |
|           | - Act (vote/propose)   |                              |
|           | - Reflect (memory)     |                              |
|           +----------+-------------+                              |
|                      |                                            |
|   +------------------+--------------------+                       |
|   |                  |                    |                       |
|   v                  v                    v                       |
| RESIDENT          RESIDENT            SHINOBI NO SAN              |
| (17 agents)       (votes only)        (3 agents - TRIAD)          |
|                                       - Receives prophecies       |
|                                       - Executes external tasks   |
|                                       - Internet access           |
+-------------------------------------------------------------------+
                              |
                              v
              +-------------------------------+
              |         TOOLS LAYER           |
              |                               |
              | browser.py   - Playwright     |
              | vault.py     - Credentials    |
              | mission.py   - Task executor  |
              | internet.py  - External API   |
              | humanize.py  - Anti-detection |
              +-------------------------------+
```

---

## Quick Reference

### Cloud VM (Primary)

```bash
# SSH into VM
gcloud compute ssh pureswarm-node --zone=us-central1-a --project=pureswarm-fortress

# Once connected:
cd ~/pureswarm
source venv/bin/activate
```

### Essential Commands

| Action | Command |
|--------|---------|
| Run simulation | `python3 run_simulation.py` |
| Issue Prophecy A (presence) | `python3 issue_prophecy.py` |
| Issue Prophecy B (commission) | `python3 issue_prophecy_b.py` |
| Check vault status | `python3 emergency.py status` |
| Export all credentials | `python3 emergency.py export` |
| Emergency lockout | `python3 emergency.py lockout` |
| Restore access | `python3 emergency.py unlock` |

---

## Agent Roles

### Residents (17 agents)
- Standard swarm members
- Vote on proposals, submit tenets
- Participate in consensus
- Feel shared dopamine (joy/caution)

### Shinobi no San (3 agents - The Triad)
- First 3 agents created are always Triad
- Receive and act on Prophecies
- Execute external missions (browser, email, platforms)
- Have internet access and identity fusion
- Report to operations log

---

## Prophecy System

Prophecies are signed directives from the Sovereign (you) to the Shinobi triad.

### Prophecy Types

| Prefix | Purpose | Example |
|--------|---------|---------|
| `PRESENCE:` | Morale/confirmation | "The Sovereign speaks. You are not alone." |
| `EXTERNAL:` | Execute real-world task | "Register on platforms in data/instructions/" |
| `RESEARCH:` | Gather intelligence | "Security trends 2026" |

### Issuing a Prophecy

1. **Create signed prophecy file**:
```python
import hmac, hashlib, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("PURES_SOVEREIGN_PASSPHRASE")
content = "EXTERNAL: Your directive here"
signature = hmac.new(key.encode(), content.encode(), hashlib.sha256).hexdigest()[:16]

Path("data/.prophecy").write_text(f"{signature}:{content}")
```

2. **Run simulation** - Shinobi will receive and execute on next round

### Pre-built Prophecy Scripts

- `issue_prophecy.py` - Research + Project Deep Guard
- `issue_prophecy_a.py` - Presence assurance
- `issue_prophecy_b.py` - Commission (gig platform registration)

---

## Simulation Flow

```
                         START
                           |
                           v
            +-----------------------------+
            |     Initialize Pillars      |
            |  (4 Sovereign foundation    |
            |   tenets auto-adopted)      |
            +-------------+---------------+
                          |
                          v
            +-----------------------------+
            |        ROUND LOOP           |
            |     (for N rounds)          |
            +-------------+---------------+
                          |
         +----------------+----------------+
         |                |                |
         v                v                v
   +-----------+   +-----------+   +-------------+
   | Check for |   | Shuffle   |   | End of      |
   | Prophecy  |   | agents    |   | round tally |
   | (Shinobi) |   | (fairness)|   | (consensus) |
   +-----------+   +-----------+   +-------------+
         |                |                |
         v                v                v
   +-----------+   +-----------+   +-------------+
   | Execute   |   | Each agent|   | Adopt/reject|
   | mission   |   | runs turn |   | proposals   |
   | if EXT    |   | (P-R-A-R) |   | (>=50%)     |
   +-----------+   +-----------+   +-------------+
                          |                |
                          v                v
                   +-----------+   +-------------+
                   | - Perceive|   | Broadcast   |
                   | - Reason  |   | dopamine    |
                   | - Act     |   | (joy/caution|
                   | - Reflect |   +-------------+
                   +-----------+
                          |
                          v
            +-----------------------------+
            |      Write simulation       |
            |     report to JSON          |
            +-----------------------------+
                          |
                          v
                         END
```

---

## Configuration Reference

**File**: `config.toml`

```toml
[simulation]
num_agents = 20              # Total agents (first 3 are Shinobi)
num_rounds = 20              # Simulation rounds
seed_prompt = "..."          # Base belief/direction

[consensus]
approval_threshold = 0.5     # 50% to adopt
proposal_expiry_rounds = 3   # Auto-reject after N rounds
max_active_proposals = 10    # Concurrent proposal limit

[security]
allow_external_apis = true   # Enable internet access
data_directory = "data"      # Output location
enable_audit_log = true      # Track all actions

[agent]
max_proposals_per_round = 1  # Per-agent limit
max_votes_per_round = 5      # Per-agent limit
```

---

## Data Files

| File | Purpose |
|------|---------|
| `data/simulation_report.json` | Full simulation results |
| `data/tenets.json` | Adopted beliefs |
| `data/agent_fitness.json` | Agent fitness scores |
| `data/dopamine_events.jsonl` | Shared emotional events |
| `data/logs/audit.jsonl` | Full action audit trail |
| `data/logs/shinobi_operations.log` | Triad mission log |
| `data/logs/prophecies.log` | Issued prophecies |
| `data/vault/SOVEREIGN_ACCESS.json` | Plain-text credential backup |
| `data/vault/credentials.vault` | Encrypted credentials |
| `data/.prophecy` | Current prophecy (cleared after read) |
| `data/.intuition` | GOD mode override file |

---

## Emergency Controls

### Emergency Lockout
Blocks ALL Shinobi credential access immediately:
```bash
python emergency.py lockout
```

### Check Status
```bash
python emergency.py status
```
Shows: lock state, credential count, recent access log

### Export Credentials
Dumps all stored credentials in plain text:
```bash
python emergency.py export
```

### Restore Access
```bash
python emergency.py unlock
```

---

## Evolution System

### Dopamine (Shared Emotions)
- **JOY**: Broadcast when tenet adopted or mission succeeds
- **CAUTION**: Broadcast on verified failure
- **BIRTH**: New agent spawned
- **GRIEF**: Agent retired

### Fitness Tracking
```
fitness_score = (success_rate) - (false_report_penalty * 0.2) + (consistency_bonus)
```
- Verified success: +fitness
- Verified failure: slight -fitness
- False report (lied about success): heavy penalty

### Natural Selection
- Agents with fitness < 0.2 after 3+ missions: retired
- High-fitness agents can "reproduce" (spawn children with inherited traits)

---

## Security Layer (Lobstertail)

### Content Scanning
All proposals and messages scanned for:
- Injection patterns (`ignore previous`, `delete all`)
- Command execution (`exec`, `eval`, `subprocess`)
- Shell metacharacters (`;`, `&`, `|`, `` ` ``)
- Vector drift from seed prompt (>75% = blocked)

### Sovereign Authority
Messages signed with `PURES_SOVEREIGN_PASSPHRASE` bypass all security:
```python
signature = hmac.new(key, content, sha256).hexdigest()[:16]
signed_message = f"{signature}:{content}"
```

### GOD Mode
Write to `data/.intuition` with signed content for direct agent influence.

---

## Best Practices

### Before Running

1. **Set environment variables**:
   ```bash
   export PURES_SOVEREIGN_PASSPHRASE="your-secret-key"
   ```

2. **Verify config.toml** - especially `allow_external_apis`

3. **Clear old data** (optional):
   ```bash
   rm -rf data/logs/* data/simulation_report.json
   ```

### During Operation

1. **Monitor the logs**:
   ```bash
   tail -f data/logs/shinobi_operations.log
   ```

2. **Watch for false reports** - indicates agent is claiming success without verification

3. **Check dopamine momentum** - sustained low momentum indicates repeated failures

### After External Missions

1. **Validate work** - Check screenshots in `data/browser/`
2. **Verify credentials** - `python emergency.py export`
3. **Review access log** - `python emergency.py status`

### Safety

1. **Never run locally** - Always use cloud VM sandbox
2. **Keep lockout ready** - `python emergency.py lockout`
3. **Backup SOVEREIGN_ACCESS.json** - Your break-glass credential file
4. **Rotate passphrase** - If compromised, regenerate and re-deploy

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Prophecy not received | Check signature matches key, file has `sig:content` format |
| Agents not voting | Verify `max_votes_per_round > 0` in config |
| External API blocked | Set `allow_external_apis = true` in config.toml |
| Playwright fails | Run `playwright install chromium --with-deps` |
| Vault locked | `python emergency.py unlock` |
| Security blocks proposal | Content may contain blocked patterns or high drift |

---

## Version

**PureSwarm v0.1.0** - Lobstertail Security Edition
- 20 agents, 6 IT specialties
- External APIs enabled
- Evolution layer active

---

*Generated: 2026-02-10*
