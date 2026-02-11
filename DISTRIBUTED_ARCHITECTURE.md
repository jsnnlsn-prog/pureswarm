# PureSwarm + OpenClaw + Dynomite: Distributed Architecture

## Overview

A distributed AI agent swarm with multi-channel messaging, consensus-driven intelligence, and fault-tolerant state management.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CHANNEL LAYER                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ OpenClaw VM1 │ │ OpenClaw VM2 │ │ OpenClaw VM3 │ │ OpenClaw VMn │        │
│  │   WhatsApp   │ │   Telegram   │ │   Discord    │ │    Slack     │        │
│  │   :18789     │ │   :18789     │ │   :18789     │ │   :18789     │        │
│  │              │ │              │ │              │ │              │        │
│  │ sandbox:all  │ │ sandbox:all  │ │ sandbox:all  │ │ sandbox:all  │        │
│  │ scope:session│ │ scope:session│ │ scope:session│ │ scope:session│        │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘        │
│         │                │                │                │                 │
│         └────────────────┴────────┬───────┴────────────────┘                 │
│                                   │ WebSocket (TLS)                          │
│                                   │ Origin validation                        │
└───────────────────────────────────┼──────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────────┐
│                           PURESWARM BRIDGE                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  WebSocket Aggregator                                                │    │
│  │  • Connects to all OpenClaw Gateway instances                       │    │
│  │  • Validates origin headers (CVE-2026-25253 mitigation)             │    │
│  │  • Rate limiting per sender (anti-bot flood)                        │    │
│  │  • Message normalization → PureSwarm Message format                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Security Layer                                                      │    │
│  │  • Token rotation (short-lived, stored in Dynomite with TTL)        │    │
│  │  • No credentials in message content (use Vault references)         │    │
│  │  • Encrypt sensitive fields before storage                          │    │
│  │  • Append-only audit log (tamper-evident)                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────────┐
│                           DYNOMITE CLUSTER                                   │
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │   Dynomite 1    │◄──►│   Dynomite 2    │◄──►│   Dynomite 3    │          │
│  │   (Rack: r1)    │    │   (Rack: r2)    │    │   (Rack: r3)    │          │
│  │                 │    │                 │    │                 │          │
│  │  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │          │
│  │  │   Redis   │  │    │  │   Redis   │  │    │  │   Redis   │  │          │
│  │  │  AUTH +   │  │    │  │  AUTH +   │  │    │  │  AUTH +   │  │          │
│  │  │  TLS      │  │    │  │  TLS      │  │    │  │  TLS      │  │          │
│  │  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │          │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘          │
│                                                                              │
│  PRIVATE SUBNET ONLY - No public exposure                                   │
│  Network: 10.0.1.0/24                                                       │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────────┐
│                        PURESWARM AGENT CLUSTER                               │
│                                                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Agent 1 │ │ Agent 2 │ │ Agent 3 │ │ Agent 4 │ │ Agent n │ │   ...   │   │
│  │ (Pod/VM)│ │ (Pod/VM)│ │ (Pod/VM)│ │ (Pod/VM)│ │ (Pod/VM)│ │         │   │
│  │         │ │         │ │         │ │         │ │         │ │         │   │
│  │ perceive│ │ perceive│ │ perceive│ │ perceive│ │ perceive│ │         │   │
│  │ reason  │ │ reason  │ │ reason  │ │ reason  │ │ reason  │ │         │   │
│  │ act     │ │ act     │ │ act     │ │ act     │ │ act     │ │         │   │
│  │ reflect │ │ reflect │ │ reflect │ │ reflect │ │ reflect │ │         │   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
│       │          │          │          │          │          │            │
│       └──────────┴──────────┴────┬─────┴──────────┴──────────┘            │
│                                  │                                         │
│                          ┌───────▼───────┐                                 │
│                          │   CONSENSUS   │                                 │
│                          │   PROTOCOL    │                                 │
│                          │               │                                 │
│                          │ • Proposals   │                                 │
│                          │ • Voting      │                                 │
│                          │ • Tenet mgmt  │                                 │
│                          └───────────────┘                                 │
│                                                                             │
│  Agents can run ANYWHERE - they just need Dynomite access                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Dynomite Schema

### Key Namespaces

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ NAMESPACE                    │ TYPE    │ PURPOSE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ tenets:shared                │ HASH    │ Consensus-approved beliefs         │
│ tenets:pending               │ HASH    │ Proposals awaiting votes           │
│ votes:{proposal_id}          │ SET     │ Agent votes per proposal           │
│                              │         │                                    │
│ sessions:{channel}:{sender}  │ HASH    │ Session state per user             │
│ transcripts:{session_id}     │ LIST    │ JSONL audit log (append-only)      │
│ memory:{agent_id}            │ HASH    │ Agent-specific knowledge           │
│                              │         │                                    │
│ messages:inbox:{agent_id}    │ LIST    │ Inbound message queue              │
│ messages:outbox:{channel}    │ LIST    │ Outbound to OpenClaw               │
│                              │         │                                    │
│ agents:registry              │ HASH    │ Active agents + heartbeat          │
│ agents:auth:{agent_id}       │ STRING  │ Encrypted auth tokens (TTL)        │
│                              │         │                                    │
│ audit:log                    │ STREAM  │ Redis Stream for audit trail       │
│ locks:{resource}             │ STRING  │ Distributed locks (SETNX + TTL)    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Models

```python
# Tenet (consensus-approved belief)
{
    "id": "tenet_001",
    "text": "Agents should prioritize user privacy",
    "proposed_by": "agent_alpha",
    "approved_at": "2026-02-10T12:00:00Z",
    "votes_for": 15,
    "votes_against": 3,
    "consensus_round": 42
}

# Proposal (pending vote)
{
    "id": "prop_123",
    "text": "We should implement rate limiting",
    "proposed_by": "agent_beta",
    "created_at": "2026-02-10T11:55:00Z",
    "expires_at": "2026-02-10T12:55:00Z",
    "status": "voting"
}

# Session (per user)
{
    "session_id": "sess_abc123",
    "channel": "whatsapp",
    "sender": "+15555550123",
    "agent_id": "agent_gamma",
    "created_at": "2026-02-10T10:00:00Z",
    "last_activity": "2026-02-10T11:30:00Z",
    "context_tokens": 4500
}

# Transcript Entry (audit log)
{
    "timestamp": "2026-02-10T11:30:00Z",
    "session_id": "sess_abc123",
    "type": "user_message",
    "channel": "whatsapp",
    "sender": "+15555550123",
    "content_hash": "sha256:abc123...",  # Content encrypted separately
    "agent_id": "agent_gamma"
}
```

## Security Model

### Threat Mitigations

| Threat | Mitigation |
|--------|------------|
| **CVE-2026-25253 (RCE)** | Origin validation on WebSocket, sandbox mode:all |
| **Token theft** | Short-lived tokens (15min TTL), stored encrypted in Dynomite |
| **Credential exposure** | Vault integration, never store in message content |
| **Data exfiltration** | Private subnet, no public Dynomite exposure |
| **Prompt injection** | Input sanitization, consensus-gated actions |
| **Bot flooding** | Rate limiting per sender, CAPTCHA on registration |
| **Write attacks** | Append-only audit log, consensus-required for tenets |
| **Moltbook-style breach** | No client-side keys, Redis AUTH + TLS |

### Network Segmentation

```
┌─────────────────────────────────────────────────────────────────┐
│                         PUBLIC INTERNET                          │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ HTTPS (443)
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DMZ (10.0.0.0/24)                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              REVERSE PROXY / WAF                          │   │
│  │  • Rate limiting                                          │   │
│  │  • Origin validation                                      │   │
│  │  • TLS termination                                        │   │
│  │  • Request sanitization                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ Internal (8080)
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   APP TIER (10.0.1.0/24)                        │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ OpenClaw 1 │  │ OpenClaw 2 │  │ OpenClaw n │                │
│  └────────────┘  └────────────┘  └────────────┘                │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    PURESWARM BRIDGE                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │  Agent 1   │  │  Agent 2   │  │  Agent n   │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ Redis Protocol (6379) + TLS
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DATA TIER (10.0.2.0/24)                       │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Dynomite 1  │  │ Dynomite 2  │  │ Dynomite 3  │             │
│  │   + Redis   │  │   + Redis   │  │   + Redis   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  NO INTERNET ACCESS - Private subnet only                       │
└─────────────────────────────────────────────────────────────────┘
```

## OpenClaw Configuration Template

Each OpenClaw VM uses this base configuration:

```json5
// ~/.openclaw/openclaw.json
{
  // Gateway security
  gateway: {
    port: 18789,
    auth: {
      token: "${OPENCLAW_GATEWAY_TOKEN}"  // From Vault, rotated daily
    }
  },

  // Strict sandboxing (CVE-2026-25253 mitigation)
  agents: {
    defaults: {
      workspace: "~/.openclaw/workspace",
      sandbox: {
        mode: "all",           // Sandbox everything
        scope: "session",      // Per-session isolation
        workspaceAccess: "ro", // Read-only by default
        docker: {
          network: "none",     // No network from sandbox
          limits: {
            memory: "512m",
            cpus: "0.5",
            pids: 100
          }
        }
      }
    },
    list: [
      {
        id: "pureswarm-bridge",
        default: true,
        identity: {
          name: "PureSwarm",
          emoji: "🐝"
        },
        // Route to PureSwarm instead of local agent
        // Custom skill handles the bridge
      }
    ]
  },

  // Channel-specific settings
  channels: {
    whatsapp: {
      dmPolicy: "allowlist",
      allowFrom: ["${ALLOWED_NUMBERS}"],
      sendReadReceipts: false,
      groups: {
        "*": { requireMention: true }
      }
    },
    telegram: {
      dmPolicy: "allowlist",
      groups: {
        "*": { requireMention: true }
      }
    },
    discord: {
      dm: { policy: "allowlist" },
      guilds: {
        "*": { requireMention: true }
      }
    }
  },

  // Tool restrictions
  tools: {
    deny: [
      "exec",        // No shell access
      "process",     // No process management
      "elevated",    // No elevated execution
    ],
    elevated: {
      enabled: false  // Never allow elevated exec
    }
  },

  // Logging
  logging: {
    level: "info",
    redactSensitive: "tools",
    file: "/var/log/openclaw/gateway.log"
  },

  // Environment
  env: {
    shellEnv: { enabled: false }  // Don't import shell env
  }
}
```

## Bridge Implementation

### Python WebSocket Aggregator

```python
# pureswarm/bridge/aggregator.py

import asyncio
import websockets
import json
from typing import Dict, Set
from dataclasses import dataclass
from cryptography.fernet import Fernet

@dataclass
class OpenClawConnection:
    """Represents a connection to an OpenClaw Gateway"""
    url: str
    token: str
    channel: str
    websocket: websockets.WebSocketClientProtocol = None

class BridgeAggregator:
    """
    Aggregates WebSocket connections from multiple OpenClaw instances
    and routes messages to/from PureSwarm.
    """

    def __init__(self, dynomite_client, config: dict):
        self.dynomite = dynomite_client
        self.config = config
        self.connections: Dict[str, OpenClawConnection] = {}
        self.message_queue = asyncio.Queue()
        self.encryption_key = Fernet(config['encryption_key'])

    async def connect_to_gateway(self, conn: OpenClawConnection):
        """Establish WebSocket connection to an OpenClaw Gateway"""

        # Origin validation (CVE-2026-25253 mitigation)
        headers = {
            'Authorization': f'Bearer {conn.token}',
            'Origin': self.config['allowed_origin']
        }

        try:
            conn.websocket = await websockets.connect(
                conn.url,
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10
            )

            # Send connect frame
            await conn.websocket.send(json.dumps({
                'type': 'connect',
                'role': 'bridge',
                'version': '1.0'
            }))

            # Wait for ack
            response = await conn.websocket.recv()
            ack = json.loads(response)

            if ack.get('type') != 'connected':
                raise ConnectionError(f"Gateway rejected connection: {ack}")

            self.connections[conn.channel] = conn

            # Start listening
            asyncio.create_task(self._listen(conn))

        except Exception as e:
            await self._log_audit('connection_failed', {
                'channel': conn.channel,
                'error': str(e)
            })
            raise

    async def _listen(self, conn: OpenClawConnection):
        """Listen for messages from an OpenClaw Gateway"""

        try:
            async for message in conn.websocket:
                data = json.loads(message)

                # Rate limiting check
                sender = data.get('sender', 'unknown')
                if not await self._check_rate_limit(sender):
                    await self._log_audit('rate_limited', {
                        'sender': sender,
                        'channel': conn.channel
                    })
                    continue

                # Normalize to PureSwarm format
                normalized = self._normalize_message(data, conn.channel)

                # Encrypt sensitive content before storage
                normalized['content_encrypted'] = self.encryption_key.encrypt(
                    normalized['content'].encode()
                ).decode()
                del normalized['content']  # Don't store plaintext

                # Queue for processing
                await self.message_queue.put(normalized)

                # Append to audit log
                await self._log_audit('message_received', {
                    'session_id': normalized['session_id'],
                    'channel': conn.channel,
                    'content_hash': normalized.get('content_hash')
                })

        except websockets.ConnectionClosed:
            await self._log_audit('connection_closed', {'channel': conn.channel})
            # Attempt reconnection
            await self._reconnect(conn)

    async def _check_rate_limit(self, sender: str) -> bool:
        """Check rate limit for sender using Dynomite"""
        key = f"ratelimit:{sender}"

        # Sliding window rate limit
        current = await self.dynomite.incr(key)
        if current == 1:
            await self.dynomite.expire(key, 60)  # 60 second window

        return current <= self.config.get('rate_limit', 30)

    def _normalize_message(self, data: dict, channel: str) -> dict:
        """Convert OpenClaw message to PureSwarm format"""
        import hashlib

        content = data.get('content', '')

        return {
            'id': data.get('id'),
            'session_id': f"{channel}:{data.get('sender')}",
            'channel': channel,
            'sender': data.get('sender'),
            'content_hash': hashlib.sha256(content.encode()).hexdigest(),
            'timestamp': data.get('timestamp'),
            'type': 'user_message'
        }

    async def _log_audit(self, event_type: str, data: dict):
        """Append to audit stream in Dynomite"""
        import time

        entry = {
            'type': event_type,
            'timestamp': time.time(),
            **data
        }

        # Redis XADD for append-only audit log
        await self.dynomite.xadd('audit:log', entry)

    async def send_response(self, channel: str, sender: str, content: str):
        """Send response back through OpenClaw"""

        if channel not in self.connections:
            raise ValueError(f"No connection for channel: {channel}")

        conn = self.connections[channel]

        await conn.websocket.send(json.dumps({
            'type': 'req',
            'method': 'send',
            'params': {
                'to': sender,
                'content': content
            }
        }))

        await self._log_audit('message_sent', {
            'channel': channel,
            'recipient': sender
        })
```

## Deployment

### Docker Compose (Local Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Dynomite Cluster
  dynomite-1:
    image: dynomitedb/dynomite:latest
    container_name: dynomite-1
    ports:
      - "8101:8101"   # Dynomite
      - "8102:8102"   # Dynomite admin
    volumes:
      - ./config/dynomite-1.yml:/etc/dynomite/dynomite.yml
      - dynomite-1-data:/var/lib/redis
    networks:
      pureswarm-net:
        ipv4_address: 10.0.2.11
    depends_on:
      - redis-1

  dynomite-2:
    image: dynomitedb/dynomite:latest
    container_name: dynomite-2
    ports:
      - "8201:8101"
      - "8202:8102"
    volumes:
      - ./config/dynomite-2.yml:/etc/dynomite/dynomite.yml
      - dynomite-2-data:/var/lib/redis
    networks:
      pureswarm-net:
        ipv4_address: 10.0.2.12
    depends_on:
      - redis-2

  dynomite-3:
    image: dynomitedb/dynomite:latest
    container_name: dynomite-3
    ports:
      - "8301:8101"
      - "8302:8102"
    volumes:
      - ./config/dynomite-3.yml:/etc/dynomite/dynomite.yml
      - dynomite-3-data:/var/lib/redis
    networks:
      pureswarm-net:
        ipv4_address: 10.0.2.13
    depends_on:
      - redis-3

  # Redis backends
  redis-1:
    image: redis:7-alpine
    container_name: redis-1
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis-1-data:/data
    networks:
      pureswarm-net:
        ipv4_address: 10.0.2.21

  redis-2:
    image: redis:7-alpine
    container_name: redis-2
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis-2-data:/data
    networks:
      pureswarm-net:
        ipv4_address: 10.0.2.22

  redis-3:
    image: redis:7-alpine
    container_name: redis-3
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis-3-data:/data
    networks:
      pureswarm-net:
        ipv4_address: 10.0.2.23

  # PureSwarm Bridge
  pureswarm-bridge:
    build: ./pureswarm
    container_name: pureswarm-bridge
    environment:
      - DYNOMITE_HOSTS=10.0.2.11:8101,10.0.2.12:8101,10.0.2.13:8101
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - OPENCLAW_GATEWAYS=${OPENCLAW_GATEWAYS}
    depends_on:
      - dynomite-1
      - dynomite-2
      - dynomite-3
    networks:
      pureswarm-net:
        ipv4_address: 10.0.1.10

  # PureSwarm Agents (scalable)
  pureswarm-agent:
    build: ./pureswarm
    command: python -m pureswarm.agent
    deploy:
      replicas: 5
    environment:
      - DYNOMITE_HOSTS=10.0.2.11:8101,10.0.2.12:8101,10.0.2.13:8101
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - AGENT_ID=${AGENT_ID:-auto}
    depends_on:
      - pureswarm-bridge
    networks:
      - pureswarm-net

networks:
  pureswarm-net:
    driver: bridge
    ipam:
      config:
        - subnet: 10.0.0.0/16

volumes:
  dynomite-1-data:
  dynomite-2-data:
  dynomite-3-data:
  redis-1-data:
  redis-2-data:
  redis-3-data:
```

## Security Checklist

Before deploying:

- [ ] Patch OpenClaw to v2026.1.24-1+ (CVE-2026-25253)
- [ ] Generate strong REDIS_PASSWORD (32+ chars)
- [ ] Generate ENCRYPTION_KEY via `Fernet.generate_key()`
- [ ] Configure TLS for Redis connections
- [ ] Set up Vault for secret management
- [ ] Enable Redis AUTH on all nodes
- [ ] Configure firewall rules (private subnet only for data tier)
- [ ] Set up audit log retention policy
- [ ] Configure rate limiting thresholds
- [ ] Test consensus protocol under load
- [ ] Verify agent authentication flow
- [ ] Set up monitoring/alerting

## Migration from Local PureSwarm

1. Export existing tenets.json to Dynomite
2. Migrate audit logs to Redis Streams
3. Update memory.py to use Dynomite client
4. Deploy Bridge as new entry point
5. Configure OpenClaw instances
6. Test end-to-end message flow
7. Gradually route traffic to new architecture

## References

- [OpenClaw Configuration](https://docs.openclaw.ai/gateway/configuration)
- [CVE-2026-25253 Advisory](https://socradar.io/blog/cve-2026-25253-rce-openclaw-auth-token/)
- [Moltbook Breach Analysis](https://www.wiz.io/blog/exposed-moltbook-database-reveals-millions-of-api-keys)
- [Dynomite Documentation](https://github.com/Netflix/dynomite)
- [PureSwarm CLAUDE.md](./CLAUDE.md)
