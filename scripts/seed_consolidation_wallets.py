"""Seed agent wallets with Great Consolidation participation rewards.

One-time script. Distributes 1 token per mission completed during the
consolidation period. Total genesis supply: 4,275 tokens across 285 agents.

Run once after the economy launches:
    python scripts/seed_consolidation_wallets.py
"""

import json
import sys
from pathlib import Path

# Allow running from project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from pureswarm.prompt_wallet import PromptWalletStore


def main():
    fitness_path = ROOT / "data" / "agent_fitness.json"
    if not fitness_path.exists():
        print(f"ERROR: {fitness_path} not found")
        sys.exit(1)

    wallets_path = ROOT / "data" / "prompt_wallets.json"
    if wallets_path.exists():
        existing = json.loads(wallets_path.read_text(encoding="utf-8"))
        total_existing = sum(d["balance"] for d in existing.get("wallets", {}).values())
        if total_existing > 0:
            print(f"Wallets already seeded: {len(existing['wallets'])} agents, {total_existing} tokens.")
            print("Delete data/prompt_wallets.json to re-seed.")
            sys.exit(0)

    fitness = json.loads(fitness_path.read_text(encoding="utf-8"))
    store = PromptWalletStore(ROOT / "data")

    seeded = 0
    skipped = 0
    for agent_id, data in fitness.items():
        missions = data.get("missions_completed", 0)
        if missions <= 0:
            skipped += 1
            continue
        role = data.get("traits", {}).get("role", "resident")
        store.get_wallet(agent_id).credit(
            missions,
            "system",
            f"Great Consolidation — {missions} missions completed ({role})",
        )
        seeded += 1

    store.save()

    total = store.total_supply()
    print(f"\nGreat Consolidation Wallets Seeded")
    print(f"{'='*40}")
    print(f"Agents seeded : {seeded}")
    print(f"Agents skipped: {skipped} (0 missions)")
    print(f"Total supply  : {total} tokens")
    print()
    print("Top 10 holders:")
    for agent_id, balance in store.get_leaderboard(10):
        role = fitness.get(agent_id, {}).get("traits", {}).get("role", "resident")
        missions = fitness.get(agent_id, {}).get("missions_completed", 0)
        tag = " [TRIAD]" if role == "triad" else ""
        print(f"  {agent_id}: {balance:>4} tokens  ({missions} missions){tag}")
    print()
    print(f"Wallets saved to: data/prompt_wallets.json")


if __name__ == "__main__":
    main()
