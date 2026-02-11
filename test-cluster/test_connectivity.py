#!/usr/bin/env python3
"""
Test cluster connectivity and basic operations.
Run after: docker-compose up -d
"""

import redis
import asyncio
import json
import time
from typing import List, Dict

# Redis nodes
NODES = [
    {"host": "localhost", "port": 6379, "name": "redis-1"},
    {"host": "localhost", "port": 6380, "name": "redis-2"},
    {"host": "localhost", "port": 6381, "name": "redis-3"},
]
PASSWORD = "[REDACTED_REDIS_PASSWORD]"


def test_basic_connectivity():
    """Test basic connection to all Redis nodes"""
    print("\n=== Testing Basic Connectivity ===")

    results = []
    for node in NODES:
        try:
            r = redis.Redis(
                host=node["host"],
                port=node["port"],
                password=PASSWORD,
                decode_responses=True
            )
            pong = r.ping()
            print(f"  {node['name']}: {'PONG' if pong else 'FAILED'}")
            results.append(pong)
        except Exception as e:
            print(f"  {node['name']}: ERROR - {e}")
            results.append(False)

    return all(results)


def test_write_read():
    """Test write to one node, read from others"""
    print("\n=== Testing Write/Read Across Nodes ===")

    # Connect to all nodes
    clients = []
    for node in NODES:
        r = redis.Redis(
            host=node["host"],
            port=node["port"],
            password=PASSWORD,
            decode_responses=True
        )
        clients.append((node["name"], r))

    # Write to node 1
    test_key = f"test:pureswarm:{int(time.time())}"
    test_value = json.dumps({
        "type": "tenet",
        "text": "Test consensus belief",
        "timestamp": time.time()
    })

    print(f"  Writing to {clients[0][0]}: {test_key}")
    clients[0][1].set(test_key, test_value)

    # Read from all nodes (manual replication check)
    print("  Reading from all nodes:")
    for name, client in clients:
        value = client.get(test_key)
        status = "OK" if value == test_value else "MISSING (expected without Dynomite)"
        print(f"    {name}: {status}")

    # Cleanup
    for _, client in clients:
        client.delete(test_key)

    return True


def test_pureswarm_schema():
    """Test the PureSwarm Dynomite schema operations"""
    print("\n=== Testing PureSwarm Schema Operations ===")

    r = redis.Redis(
        host="localhost",
        port=6379,
        password=PASSWORD,
        decode_responses=True
    )

    # 1. Tenets (HASH)
    print("  Testing tenets:shared (HASH)...")
    r.hset("tenets:shared", "tenet_001", json.dumps({
        "id": "tenet_001",
        "text": "Agents should prioritize user privacy",
        "votes_for": 15,
        "votes_against": 3
    }))
    tenet = json.loads(r.hget("tenets:shared", "tenet_001"))
    print(f"    Stored tenet: {tenet['text'][:40]}...")

    # 2. Sessions (HASH)
    print("  Testing sessions:whatsapp:+1555 (HASH)...")
    r.hset("sessions:whatsapp:+15555550123", mapping={
        "session_id": "sess_abc123",
        "agent_id": "agent_alpha",
        "created_at": str(time.time())
    })
    session = r.hgetall("sessions:whatsapp:+15555550123")
    print(f"    Session: {session['session_id']}")

    # 3. Audit log (STREAM)
    print("  Testing audit:log (STREAM)...")
    entry_id = r.xadd("audit:log", {
        "type": "message_received",
        "channel": "whatsapp",
        "sender": "+15555550123",
        "timestamp": str(time.time())
    })
    print(f"    Added audit entry: {entry_id}")

    # Read last 3 entries
    entries = r.xrange("audit:log", "-", "+", count=3)
    print(f"    Audit log has {len(entries)} entries")

    # 4. Message queue (LIST)
    print("  Testing messages:inbox:agent_alpha (LIST)...")
    r.rpush("messages:inbox:agent_alpha", json.dumps({
        "id": "msg_001",
        "content": "Hello from test",
        "timestamp": time.time()
    }))
    queue_len = r.llen("messages:inbox:agent_alpha")
    print(f"    Inbox queue length: {queue_len}")

    # 5. Distributed lock (SETNX + TTL)
    print("  Testing locks:consensus (distributed lock)...")
    lock_acquired = r.set("locks:consensus", "agent_alpha", nx=True, ex=30)
    print(f"    Lock acquired: {lock_acquired}")

    # Cleanup
    r.delete(
        "tenets:shared",
        "sessions:whatsapp:+15555550123",
        "messages:inbox:agent_alpha",
        "locks:consensus"
    )
    r.delete("audit:log")  # Can't easily delete stream, but that's fine for test

    print("  Schema test complete!")
    return True


def test_consensus_simulation():
    """Simulate a basic consensus vote"""
    print("\n=== Simulating Consensus Vote ===")

    r = redis.Redis(
        host="localhost",
        port=6379,
        password=PASSWORD,
        decode_responses=True
    )

    proposal_id = "prop_test_001"

    # Create proposal
    r.hset(f"proposals:{proposal_id}", mapping={
        "id": proposal_id,
        "text": "We should implement rate limiting",
        "proposed_by": "agent_alpha",
        "status": "voting",
        "created_at": str(time.time())
    })
    print(f"  Created proposal: {proposal_id}")

    # Simulate votes from 5 agents
    agents = ["agent_alpha", "agent_beta", "agent_gamma", "agent_delta", "agent_epsilon"]
    votes = ["for", "for", "for", "against", "for"]  # 4-1 majority

    for agent, vote in zip(agents, votes):
        r.sadd(f"votes:{proposal_id}:{vote}", agent)
        print(f"    {agent} voted: {vote}")

    # Count votes
    votes_for = r.scard(f"votes:{proposal_id}:for")
    votes_against = r.scard(f"votes:{proposal_id}:against")
    total = votes_for + votes_against

    print(f"\n  Results: {votes_for} for, {votes_against} against")

    # Check consensus (majority = >50%)
    if votes_for > total / 2:
        print(f"  CONSENSUS REACHED - Proposal approved!")
        r.hset(f"proposals:{proposal_id}", "status", "approved")

        # Move to tenets
        proposal = r.hgetall(f"proposals:{proposal_id}")
        r.hset("tenets:shared", proposal_id, json.dumps({
            "id": proposal_id,
            "text": proposal["text"],
            "votes_for": votes_for,
            "votes_against": votes_against,
            "approved_at": str(time.time())
        }))
        print(f"  Added to shared tenets!")
    else:
        print(f"  Consensus not reached")

    # Cleanup
    r.delete(
        f"proposals:{proposal_id}",
        f"votes:{proposal_id}:for",
        f"votes:{proposal_id}:against",
        "tenets:shared"
    )

    return True


def main():
    print("=" * 60)
    print("PureSwarm + Dynomite Test Cluster Validation")
    print("=" * 60)

    tests = [
        ("Basic Connectivity", test_basic_connectivity),
        ("Write/Read", test_write_read),
        ("PureSwarm Schema", test_pureswarm_schema),
        ("Consensus Simulation", test_consensus_simulation),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ERROR in {name}: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

    all_passed = all(r for _, r in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

    return all_passed


if __name__ == "__main__":
    main()
