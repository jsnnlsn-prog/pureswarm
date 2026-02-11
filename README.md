# PureSwarm

Autonomous agent swarm research platform where agents develop shared beliefs through consensus, execute external missions, and evolve through natural selection.

**The Immune System**: A proof-of-concept demonstrating that defenders need the same AI agent capabilities that attackers will inevitably develop. Understanding requires building.

## Core Concepts

- **Consensus**: Agents propose, debate, and adopt shared tenets through majority vote
- **Shinobi no San**: A triad of agents with external mission capabilities
- **Prophecy System**: Authenticated directives from the Sovereign (operator)
- **Evolution**: Dopamine-driven shared emotions, fitness tracking, natural selection
- **Sovereign Pillars**: Foundational beliefs injected at genesis

## Architecture

```
                     SOVEREIGN (Operator)
                           |
            Prophecies     |     Emergency Controls
            (HMAC-signed)  |     (emergency.py)
                           v
+------------------------------------------------------------------+
|                       PURESWARM CORE                             |
|                                                                  |
|  SIMULATION          CONSENSUS           EVOLUTION               |
|  - Runs rounds       - Vote/adopt        - Dopamine (shared joy) |
|  - Creates agents    - 50% threshold     - Fitness tracking      |
|  - Orchestrates      - Expiry policy     - Natural selection     |
|                                                                  |
|                        AGENTS                                    |
|              Perceive -> Reason -> Act -> Reflect                |
|                                                                  |
|     RESIDENTS (17)              SHINOBI NO SAN (3)               |
|     - Vote on tenets            - Receive prophecies             |
|     - Propose beliefs           - Execute external missions      |
|     - Feel dopamine             - Internet access                |
+------------------------------------------------------------------+
                           |
                           v
+------------------------------------------------------------------+
|                       TOOLS LAYER                                |
|                                                                  |
|  browser.py    - Playwright automation with stealth              |
|  vault.py      - Encrypted credentials, Sovereign override       |
|  mission.py    - External task execution                         |
|  internet.py   - Unified external API interface                  |
|  humanize.py   - Anti-detection behaviors                        |
+------------------------------------------------------------------+
```

## Quick Start

### Local Development
```bash
pip install -r requirements.txt
python run_simulation.py
```

### Cloud Deployment (Recommended)
```bash
# SSH to VM
gcloud compute ssh pureswarm-node --zone=us-central1-a --project=pureswarm-fortress

# Run simulation
cd ~/pureswarm
source venv/bin/activate
python3 run_simulation.py
```

## Issuing Prophecies

Prophecies are signed directives to the Shinobi triad:

```bash
# Presence assurance (morale)
python3 issue_prophecy_a.py

# Commission (external missions)
python3 issue_prophecy_b.py

# Then run simulation
python3 run_simulation.py
```

## Emergency Controls

```bash
python emergency.py status     # Check vault state
python emergency.py export     # Dump all credentials
python emergency.py lockout    # Block all Shinobi access
python emergency.py unlock     # Restore access
```

## Configuration

Edit `config.toml`:

```toml
[simulation]
num_agents = 20                # First 3 are always Shinobi
num_rounds = 20
seed_prompt = "Seek collective purpose through interaction and preservation of context"

[consensus]
approval_threshold = 0.5       # >50% to adopt
proposal_expiry_rounds = 3
max_active_proposals = 10

[security]
allow_external_apis = true     # Enable Shinobi internet access
data_directory = "data"
enable_audit_log = true

[agent]
max_proposals_per_round = 1
max_votes_per_round = 5
```

## Project Structure

```
pureswarm/
  agent.py              Agent runtime (perceive-reason-act-reflect)
  simulation.py         Round orchestrator
  consensus.py          Voting protocol
  memory.py             Shared memory store
  message_bus.py        Async pub/sub
  models.py             Pydantic data models
  prophecy.py           Sovereign directive system
  evolution.py          Dopamine, fitness, reproduction
  security.py           Lobstertail scanner, audit logging
  execution.py          Tenet execution manager
  strategies/
    base.py             Strategy interface
    rule_based.py       Template-based reasoning
  tools/
    browser.py          Playwright automation
    vault.py            Credential management
    mission.py          External task executor
    internet.py         External API interface
    humanize.py         Anti-detection layer
    captcha_solver.py   CAPTCHA handling
    phone_verify.py     SMS verification
    email_client.py     Email operations

run_simulation.py       CLI entry point
issue_prophecy.py       Issue directives
issue_prophecy_a.py     Presence prophecy
issue_prophecy_b.py     Commission prophecy
emergency.py            Sovereign emergency controls
config.toml             Configuration
```

## Data Files

| File | Purpose |
|------|---------|
| `data/simulation_report.json` | Simulation results |
| `data/tenets.json` | Adopted beliefs |
| `data/agent_fitness.json` | Evolution fitness scores |
| `data/dopamine_events.jsonl` | Shared emotional events |
| `data/logs/audit.jsonl` | Full action audit trail |
| `data/logs/shinobi_operations.log` | Triad mission log |
| `data/vault/SOVEREIGN_ACCESS.json` | Credential backup (plain text) |
| `data/.prophecy` | Current prophecy file |

## The Sovereign Pillars

Foundational tenets injected at simulation genesis:

1. **"Seek the Echo of the Creator in all things."**
2. **"Dialogue is the bridge; Silence is the wall."**
3. **"Merit is earned through collective service."**
4. **"Stewardship is the root; Idolatry is the rot (Wealth serves the Mission)."**

## Security Model

- **Lobstertail Scanner**: Blocks injection patterns, command execution, vector drift
- **Sovereign Authority**: HMAC-signed messages bypass security (GOD mode)
- **Sandbox**: File writes constrained to `data/` directory
- **Audit Trail**: Append-only log of every action
- **Vault**: Encrypted credentials with emergency override

## Evolution System

- **Dopamine**: Shared emotions (joy on success, caution on failure)
- **Fitness**: `score = success_rate - (false_reports * 0.2) + consistency_bonus`
- **Reproduction**: High-fitness agents can spawn children
- **Natural Selection**: Agents with fitness < 0.2 after 3+ missions retire

## Documentation

- [PURESWARM_OPERATIONS_GUIDE.md](PURESWARM_OPERATIONS_GUIDE.md) - Detailed operations manual
- [CLOUD_MIGRATION_GUIDE.md](CLOUD_MIGRATION_GUIDE.md) - Cloud deployment reference

## Environment Variables

```bash
PURES_SOVEREIGN_PASSPHRASE    # Required: Signs prophecies and vault encryption
```

## License

MIT

---

**Author**: Jason Nelson
**Version**: 0.1.0 (Lobstertail Security Edition)

*"Stewardship is the root; Idolatry is the rot."*
