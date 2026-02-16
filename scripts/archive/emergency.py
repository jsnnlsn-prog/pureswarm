#!/usr/bin/env python3
"""SOVEREIGN EMERGENCY CONTROLS

Run this if Shinobi goes rogue or something breaks.

Usage:
    python emergency.py lockout     # Block all Shinobi credential access
    python emergency.py unlock      # Restore access
    python emergency.py export      # Dump all credentials to screen
    python emergency.py status      # Check current state
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from pureswarm.tools.vault import SovereignVault, quick_lockout, quick_unlock, quick_export


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()
    data_dir = Path("data")

    if command == "lockout":
        print("=" * 60)
        print("EMERGENCY LOCKOUT ACTIVATED")
        print("=" * 60)
        quick_lockout(data_dir)
        print("\nAll Shinobi credential access is now BLOCKED.")
        print("To restore: python emergency.py unlock")

    elif command == "unlock":
        quick_unlock(data_dir)
        print("Vault access restored.")

    elif command == "export":
        print(quick_export(data_dir))

    elif command == "status":
        vault = SovereignVault(data_dir)
        print("=" * 60)
        print("SOVEREIGN VAULT STATUS")
        print("=" * 60)
        print(f"Locked: {vault.is_locked()}")
        print(f"Credentials stored: {len(vault.list_credentials())}")
        print(f"Backup file: {data_dir / 'vault' / 'SOVEREIGN_ACCESS.json'}")
        print(f"Access log: {data_dir / 'vault' / 'access_log.jsonl'}")
        print()
        print("Recent access log:")
        for entry in vault.get_access_log(10):
            print(f"  {entry['timestamp']}: {entry['action']} - {entry['credential']} by {entry['accessor']}")

    elif command == "credentials":
        vault = SovereignVault(data_dir)
        creds = vault.list_credentials()
        print("=" * 60)
        print("STORED CREDENTIALS (names only, no secrets)")
        print("=" * 60)
        for c in creds:
            print(f"  [{c['type']}] {c['name']} - {c['username']}")
        print()
        print("For full details: python emergency.py export")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
