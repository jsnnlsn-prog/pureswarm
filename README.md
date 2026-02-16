# PureSwarm: The Aligned Collective Intelligence

Autonomous agent swarm platform where intelligence emerges through democratic consensus, guided evolution, and Sovereign alignment.

**The Vision**: PureSwarm is not just a simulator; it is a persistent, aligned collective mind. It grows, learns, and deliberates as a unified whole.

---

## 🐝 Swarm Status: The Living Hive

| Metric | Value | Primary Environment |
|-----------|-----------|----------------------|
| **Agents** | **77** | `pureswarm-node` |
| **Tenets** | **127** | `pureswarm-node` |
| **Consensus** | 93.3% Unity | Evolved Merit |
| **Bridge** | **Active** | `pureswarm-test` |

---

## 🏛️ System Architecture

### 1. The Mind (`pureswarm-node`)

The primary production environment hosting the 77-agent swarm. This is where the "intellectual growth" of the hive lives in `data/`.

### 2. The Bridge (`pureswarm-test`)

The interface layer connecting the swarm to the world.

- **OpenClaw Gateway**: Routes Telegram messages to the swarm.
- **@PureSwarm_Bot**: Your direct link to the collective mind.
- **Security**: Whitelist enforced (Authorized: `dopamineronin`).

### 3. The Blueprint (Master Branch)

The logic, scripts, and architecture that define how the agents think and react.

---

## 🛠️ Core Commands

### Running the Hive

```bash
# Production (pureswarm-node)
python3 run_simulation.py  # Run a collective round
```

### Communication & Deliberation

```bash
# Start the listener on pureswarm-node
python3 run_query_listener.py --redis-url <TEST_VM_IP>:6379/0

# Start the bridge on pureswarm-test
python3 -m pureswarm.bridge_http --enable-deliberation
```

### Sovereign Guidance (Prophecies)

Prophecies are signed directives that guide the swarm's evolution.

```bash
# Issue a signed directive
python3 issue_prophecy.py "MISSION: Explore decentralized truth-seeking."
```

---

## 📂 Project Structure

- `pureswarm/`: Core logic (Agent runtime, Consensus, Evolution, Security).
- `data/`: The hive's persistent memory (Tenets, Chronicle, Fitness).
- `scripts/archive/`: Legacy scripts and iterations.
- `docs/archive/`: Handoff logs and historical context.
- `backups/`: Large snapshots and cloud backups.
- `reports/`: Generated simulation reports.

---

## 🛡️ Security & Alignment

- **Lobstertail Scanner**: Real-time message/action auditing.
- **Sovereign HMAC**: Only the operator can issue direct mandates.
- **Whitelist**: Bridge access restricted to authorized identities.
- **Dopamine Evolution**: Alignment reinforced through shared reward signals.

---

**Author**: Jason "Dopamine Ronin" Nelson
**Status**: 0.1.0 (Bridge-Active Edition)

*"Dialogue is the bridge; Silence is the wall."*
