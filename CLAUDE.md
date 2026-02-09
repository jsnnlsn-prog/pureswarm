# PureSwarm

Autonomous agent swarm prototype where agents develop shared beliefs through consensus, inspired by emergent collective behavior patterns observed in AI agent populations.

## Tech Stack

- Python 3.11+ (asyncio, tomllib)
- Pydantic 2.x for data models / serialization
- pytest for testing
- No external APIs — fully self-hosted, local execution

## Project Structure

```
pureswarm/           Core library
  models.py          Pydantic data models (Tenet, Proposal, Message, etc.)
  message_bus.py     In-process async pub/sub for agent communication
  memory.py          Consensus-gated shared memory store (JSON file-backed)
  consensus.py       Voting protocol — proposals need majority to become tenets
  agent.py           Agent runtime: perceive-reason-act-reflect loop
  simulation.py      Round orchestrator, logging, report generation
  security.py        Audit logger, sandbox path enforcement
  strategies/
    base.py          Abstract reasoning strategy interface
    rule_based.py    Deterministic template + keyword scoring strategy
run_simulation.py    CLI entry point — reads config.toml, runs simulation
config.toml          Simulation parameters
data/                Runtime output (tenets.json, archive/, logs/)
tests/               pytest unit tests
```

## Running

```bash
pip install -r requirements.txt
python run_simulation.py
```

Output goes to `data/` — check `data/simulation_report.json` for results and `data/logs/audit.jsonl` for the full action trail.

## Configuration

Edit `config.toml` to adjust agent count, rounds, consensus threshold, seed prompt, etc.

## Development Conventions

- Type hints on all function signatures
- async/await for all I/O and inter-component calls
- Pydantic models for all serialized data — no raw dicts crossing module boundaries
- Shared memory writes ONLY through the consensus protocol (enforced via sentinel)
- All agent actions logged to audit trail

## Security Principles

- No external API calls unless `allow_external_apis = true` in config
- File writes sandboxed to `data/` directory
- Shared tenets are read-only to agents — writes require majority vote
- No eval/exec/subprocess from agent code paths
- Append-only audit log of every action
- Tenet text is data, never executed as code

## Testing

```bash
pytest tests/ -v
```
