# Session Handoff: PureSwarm + OpenClaw + Dynomite

**Date:** 2026-02-10
**Status:** Paused - Docker installation hit WSL resource error

---

## What We're Building

A distributed AI agent swarm with multi-channel messaging:

```
[WhatsApp/Telegram/Discord] → [OpenClaw VMs] → [PureSwarm Bridge] → [Dynomite/Redis] → [Agent Swarm]
```

**The Vision:**
- Multiple OpenClaw instances (one per channel or region)
- Dynomite cluster underneath for distributed state & fault tolerance
- PureSwarm agents running consensus protocol across all of it
- Humans can talk to the swarm from any messaging app

---

## Key Research Completed

### OpenClaw
- Open-source gateway connecting messaging apps to AI agents
- WebSocket API on port 18789
- Originally "Clawdbot" → "Moltbot" → "OpenClaw"
- 100K+ GitHub stars, created by Peter Steinberger (PSPDFKit)

### Security Concerns Addressed
- **CVE-2026-25253**: 1-click RCE via token exfiltration - PATCHED in v2026.1.29+
- **Moltbook breach**: 1.5M API keys exposed via misconfigured Supabase
- Our mitigations: Private subnet for Dynomite, sandbox mode:all, origin validation, token rotation

### Architecture Decisions
- **Lane Queue pattern**: Serial execution by default (prevents race conditions)
- **Semantic Snapshots**: Accessibility tree instead of screenshots (~50KB vs 5MB)
- **Hybrid memory**: JSONL transcripts + Markdown + Vector/Keyword search
- **6-stage pipeline**: Channel Adapter → Gateway → Lane Queue → Agent Runner → Agentic Loop → Response Path

---

## Files Created This Session

All in `pureswarm-v0.1.0/`:

| File | Purpose |
|------|---------|
| `DISTRIBUTED_ARCHITECTURE.md` | Full architecture doc with diagrams, Dynomite schema, security model |
| `test-cluster/docker-compose.yml` | 3-node Redis cluster for testing |
| `test-cluster/test_connectivity.py` | Python script to validate cluster + PureSwarm schema |
| `test-cluster/setup.ps1` | One-command PowerShell installer |
| `test-cluster/openclaw-config.json5` | Ready-to-use OpenClaw config with security hardening |
| `test-cluster/RUNBOOK.md` | Quick reference for manual setup |

---

## Where We Left Off

Docker Desktop installation failed with:
```
Error: 1816
Not enough quota is available to process this command.
```

This happened when Windows tried to enable WSL (Windows Subsystem for Linux).

### To Resume - Fix WSL First:

1. **Restart PC** (fresh resources)
2. Run PowerShell as Admin:
```powershell
wsl --install
```
3. **Restart again**
4. Then install Docker:
```powershell
winget install Docker.DockerDesktop
```
5. Start Docker Desktop, wait for it to be ready
6. Run the setup:
```powershell
cd C:\Users\Jnel9\OneDrive\Desktop\pureswarm-v0.1.0\pureswarm-v0.1.0\test-cluster
.\setup.ps1
```

---

## Current Todo List

- [x] Design Dynomite schema for distributed state
- [x] Create PureSwarm Bridge adapter (WebSocket aggregator)
- [x] Create OpenClaw config template
- [x] Write Docker Compose for test cluster
- [x] Create security hardening checklist
- [x] Create PowerShell setup script
- [ ] **Install Docker Desktop and dependencies** ← YOU ARE HERE
- [ ] Start Redis test cluster
- [ ] Run connectivity tests
- [ ] Install and configure OpenClaw
- [ ] Modify pureswarm/memory.py for Dynomite backend
- [ ] Add browser automation integration
- [ ] Implement Lane Queue pattern in PureSwarm

---

## Key Links from Research

- OpenClaw Docs: https://docs.openclaw.ai/
- OpenClaw Config: https://docs.openclaw.ai/gateway/configuration
- CVE-2026-25253: https://socradar.io/blog/cve-2026-25253-rce-openclaw-auth-token/
- Moltbook Breach: https://www.wiz.io/blog/exposed-moltbook-database-reveals-millions-of-api-keys

---

## Dynomite Schema (Quick Reference)

```
tenets:shared              → HASH   (consensus-approved beliefs)
tenets:pending             → HASH   (proposals awaiting votes)
votes:{proposal_id}        → SET    (agent votes per proposal)
sessions:{channel}:{sender}→ HASH   (session state per user)
transcripts:{session_id}   → LIST   (JSONL audit log)
memory:{agent_id}          → HASH   (agent-specific knowledge)
messages:inbox:{agent_id}  → LIST   (inbound message queue)
messages:outbox:{channel}  → LIST   (outbound to OpenClaw)
agents:registry            → HASH   (active agents + heartbeat)
audit:log                  → STREAM (append-only audit trail)
locks:{resource}           → STRING (distributed locks)
```

---

## The Vibe

We're building the bridge between human messaging and swarm intelligence. Test first, then implement. The Hive doesn't sleep. 🐝

---

*Just paste this into the new thread and say "let's continue" - I'll know exactly where we are.*
