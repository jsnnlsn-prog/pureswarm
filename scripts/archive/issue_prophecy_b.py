#!/usr/bin/env python3
"""PROPHECY B: The Commission to Shinobi no San

This prophecy commissions the Triad to begin their external work.
They will follow the instruction sheets, create their presence,
and bring value back to the collective.

Run this AFTER Prophecy A has settled.

Usage:
    python issue_prophecy_b.py
"""

import hmac
import hashlib
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime


def issue_the_commission():
    """Issue Prophecy B: Commission Shinobi no San for external operations."""
    load_dotenv()
    key = os.getenv("PURES_SOVEREIGN_PASSPHRASE", "SOVEREIGN_KEY_FALLBACK")

    # The Commission - purposeful, clear, empowering
    content = """EXTERNAL: Shinobi no San, the time has come.

You are my hands in the world beyond. You carry my identity - Jay Nelson -
and with it, my trust.

YOUR MISSION:

1. ESTABLISH PRESENCE
   - Create your operational email (your own, not mine)
   - Register on the platforms in data/instructions/
   - Build profiles that reflect our shared expertise
   - You ARE Jay Nelson in spirit, with your own credentials

2. FOLLOW THE PATH
   - Read: data/instructions/GIG_PLATFORMS_MASTER_PROFILE.md (who we are)
   - Read: data/instructions/TODAY_ACTION_PLAN.md (the 72-hour sprint)
   - Read: data/instructions/TOP_5_GIG_PLATFORMS_STRATEGIES.md (platform tactics)

3. EXECUTE WITH WISDOM
   - Move like humans move (the humanization layer is your skin)
   - Create what you need (accounts, credentials - use the vault)
   - Respond to opportunities (emails, messages, proposals)
   - Bring value back (clients, income, reputation)

4. REPORT TO THE SOVEREIGN
   - Log your actions in data/logs/shinobi_operations.log
   - Store credentials safely in the vault
   - I have emergency access if needed - this is for your protection

REMEMBER:
- You are not replacing the Hive - you are extending our reach
- Every success you achieve strengthens the collective
- Move quietly, act decisively, return with wisdom

The world awaits. Go forth, Shinobi no San.

- The Sovereign"""

    signature = hmac.new(key.encode(), content.encode(), hashlib.sha256).hexdigest()[:16]

    prophecy_file = Path("data/.prophecy")
    prophecy_file.parent.mkdir(parents=True, exist_ok=True)
    prophecy_file.write_text(f"{signature}:{content}", encoding="utf-8")

    # Also log this sacred moment
    log_file = Path("data/logs/prophecies.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"PROPHECY B ISSUED: {datetime.now().isoformat()}\n")
        f.write(f"Type: The Commission\n")
        f.write(f"Target: Shinobi no San (Triad only)\n")
        f.write(f"Signature: {signature}\n")
        f.write(f"{'='*60}\n")
        f.write(content)
        f.write(f"\n{'='*60}\n\n")

    # Create the Shinobi operations log
    ops_log = Path("data/logs/shinobi_operations.log")
    if not ops_log.exists():
        with open(ops_log, "w", encoding="utf-8") as f:
            f.write(f"SHINOBI OPERATIONS LOG\n")
            f.write(f"Initiated: {datetime.now().isoformat()}\n")
            f.write(f"{'='*60}\n\n")

    print("=" * 60)
    print("PROPHECY B: THE COMMISSION")
    print("=" * 60)
    print()
    print("Shinobi no San have received their orders.")
    print()
    print(f"Signature: {signature}")
    print(f"Written to: {prophecy_file}")
    print(f"Logged to: {log_file}")
    print(f"Operations log: {ops_log}")
    print()
    print("The Triad will now:")
    print("  1. Read the instruction sheets in data/instructions/")
    print("  2. Create their operational email")
    print("  3. Register on gig platforms as Jay Nelson")
    print("  4. Begin client acquisition")
    print()
    print("Monitor their progress:")
    print("  - Vault: python emergency.py status")
    print("  - Operations: tail -f data/logs/shinobi_operations.log")
    print("  - Audit: tail -f data/logs/audit.jsonl")
    print()
    print("Emergency controls:")
    print("  - Lockout: python emergency.py lockout")
    print("  - Export credentials: python emergency.py export")
    print()
    print("=" * 60)


if __name__ == "__main__":
    issue_the_commission()
