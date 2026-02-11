# PureSwarm Test Cluster

Minimal test environment to validate the distributed architecture before full implementation.

## Quick Start

```bash
# 1. Start the cluster
cd test-cluster
docker-compose up -d

# 2. Verify containers are running
docker ps

# 3. Run connectivity test
pip install redis
python test_connectivity.py

# 4. Manual Redis check
docker exec -it redis-1 redis-cli -a [REDACTED_REDIS_PASSWORD] PING
```

## What This Tests

| Test | Purpose |
|------|---------|
| Basic Connectivity | All 3 Redis nodes responding |
| Write/Read | Data storage works |
| PureSwarm Schema | Our key namespaces work (tenets, sessions, audit, queues, locks) |
| Consensus Simulation | Voting mechanism works in Redis |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TEST CLUSTER                          │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   redis-1   │  │   redis-2   │  │   redis-3   │     │
│  │  :6379      │  │  :6380      │  │  :6381      │     │
│  │ 172.28.0.11 │  │ 172.28.0.12 │  │ 172.28.0.13 │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              test-runner                         │    │
│  │              172.28.0.100                        │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Network: testnet (172.28.0.0/16)                       │
└─────────────────────────────────────────────────────────┘
```

## Next Steps

After tests pass:

1. **Add Dynomite** - For cross-node replication
2. **Add OpenClaw** - For messaging integration
3. **Add PureSwarm Bridge** - Connect everything

## Cleanup

```bash
docker-compose down -v
```
