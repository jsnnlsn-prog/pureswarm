# PureSwarm v0.2.0

Autonomous agent swarm where agents develop shared beliefs through consensus. Agents earn, hold, and trade sacred prompt tokens. The Great Consolidation is complete: 905 tenets pruned to 10.

## Tech Stack

- Python 3.11+ (asyncio, tomllib/tomli)
- Pydantic 2.x for data models
- Rich for dashboard rendering
- Playwright/websockets/aiohttp for external operations (Shinobi Tools)
- Redis (Optional, Phase 7+) for distributed agent memory

## Project Structure

```
pureswarm/           Core library
  agent.py           Agent runtime & perceive-reason-act-reflect loop
  bridge.py          OpenClaw bridge integration
  chronicle.py       Historical event logging
  consensus.py       Voting & tenet adoption logic
  dashboard.py       Rich-based visual HUD
  deliberation.py    Multi-agent team communication (Phase 5)
  evolution.py       Agent mutation & fitness scaling
  execution.py       ExecutionManager for async task dispatch
  memory.py          Persistent agent memory (JSON/Redis)
  message_bus.py     Async pub/sub bus
  models.py          Pydantic schemas
  prompt_economy.py  Per-squad token quotas (old economy layer)
  prompt_wallet.py   Sacred per-agent wallets, rate limiter, placement rewards (Phase 7.5)
  prophecy.py        Sovereign command & oracle system
  security.py        Audit logs & Lobstertail scanner
  simulation.py      Simulation orchestration
  squad_competition.py  Competitive consolidation logic
  tenet_clusterer.py Similarity-based tenet packaging
  workshop.py        Problem-solving environment
  strategies/        Agent reasoning patterns
    base.py          BaseStrategy interface
    rule_based.py    Deterministic resident strategy
    llm_driven.py    LLM strategy (Triad/Researcher)
  tools/             External capability modules
    http_client.py   ShinobiHTTPClient, VeniceAIClient, AnthropicClient
    internet.py      InternetAccess (role-gated)
    vault.py         Secrets management
    browser.py       Playwright automation
    email_client.py  Email operations
    mission.py       External mission executor

run_simulation.py    CLI entry point
config.toml          Main simulation config
data/                Runtime artifacts & tenets
docs/                Documentation & Prophecy Think Tank
directives/          Sovereign directives
execution/           Task execution artifacts
```

## Critical Commands

```bash
# Dashboard (Windows PowerShell ONLY)
$env:EMERGENCY_MODE="TRUE"; python -m pureswarm.dashboard

# Run consolidation (Emergency Mode)
set EMERGENCY_MODE=TRUE && python run_simulation.py --emergency --num_rounds 10

# Free roam (no new tenets, agents do what they want)
set NO_NEW_TENETS=TRUE && python run_simulation.py --num_rounds 10

# Check tenet count
python -c "import json; t=json.load(open('data/tenets.json')); print(f'Tenets: {len(t)}')"

# Check agent count
python -c "import json; f=json.load(open('data/agent_fitness.json')); print(f'Agents: {len(f)}')"

# Check wallet balances
python -c "import json; w=json.load(open('data/prompt_wallets.json')); print(json.dumps(w, indent=2))"
```

## Security Principles

- **Lobstertail Scanner**: Content filtering for injection and drift.
- **Sovereign Signature**: HMAC-based authority for user commands.
- **Audit Trail**: Every action logged to `data/logs/audit.jsonl`.
- **Sandbox**: Local file access restricted to `data/`.

## Sacred Prompt Economy (Phase 7.5)

Prompt tokens are sacred information assets — scarce, transferable, and meaningful.

- **Earning**: Squad placement rewards each round (1st=3, 2nd=2, 3rd=1 per agent)
- **Spending**: Only Triad/Researcher agents can spend 1 token per LLM call
- **Holding**: Any agent can hold tokens indefinitely
- **Giving**: Any agent can gift tokens via `PROMPT_GIFT` message (true transfer)
- **Trading**: Peer-to-peer via `PROMPT_TRADE` message, any squad
- **Rate Limit**: 8 LLM calls/minute hive-wide (configurable via `PROMPT_RATE_LIMIT` env var)
- **Persistence**: Balances stored in `data/prompt_wallets.json`

## Current Status

- **Tenets**: 10 (Great Consolidation complete — 98.9% reduction from 905. LOCKED. NO_NEW_TENETS enforced.)
- **Agents**: 285 (x2 Dopamine Flush applied)
- **Momentum**: 2.00 (Maximum Overdrive)
- **Prophecy**: Eternal Life (Path A/B/C) drafted, pending deployment

## Phase Progress

| Phase | Description | Status |
| ----- | ----------- | ------ |
| 1 | Remove auto-YES voting | DONE |
| 2 | Load real identity with specialization | DONE |
| 3 | Pass voting context to agents | DONE |
| 4 | Triad recommendation system | DONE |
| 5 | Team communication (Triad deliberation) | DONE |
| 6 | Persistent memory across sessions | DONE |
| 7 | Redis backend for agent memory | NEXT |
| 7.5 | Sacred Prompt Economy | DONE |
| 8 | Eternal Life (Path A/B/C) | PENDING |
| 9 | Fix security bypasses | PENDING |
