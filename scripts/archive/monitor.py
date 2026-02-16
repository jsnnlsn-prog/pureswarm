#!/usr/bin/env python3
"""Sovereign Monitor - Watch Shinobi operations in real-time.

Run this in a separate terminal while simulation runs:
    python monitor.py

Or on the VM:
    cd ~/pureswarm && source venv/bin/activate && python3 monitor.py
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Colors for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def read_tail(filepath: Path, n_lines: int = 20) -> list:
    """Read last n lines from a file."""
    if not filepath.exists():
        return []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            return lines[-n_lines:]
    except Exception:
        return []

def format_ops_line(line: str) -> str:
    """Format an operations log line with colors."""
    if "[SUCCESS]" in line:
        return f"{Colors.GREEN}{line}{Colors.END}"
    elif "[FAILED]" in line or "[ERROR]" in line:
        return f"{Colors.RED}{line}{Colors.END}"
    elif "[EXECUTING]" in line:
        return f"{Colors.YELLOW}{line}{Colors.END}"
    elif "PHASE" in line or "MISSION" in line:
        return f"{Colors.CYAN}{Colors.BOLD}{line}{Colors.END}"
    return line

def get_vault_summary(data_dir: Path) -> dict:
    """Get summary of stored credentials."""
    vault_file = data_dir / "vault" / "credentials.json"
    if not vault_file.exists():
        return {"count": 0, "types": {}}

    try:
        with open(vault_file, 'r') as f:
            creds = json.load(f)

        types = {}
        for cred in creds:
            t = cred.get("type", "unknown")
            types[t] = types.get(t, 0) + 1

        return {"count": len(creds), "types": types}
    except Exception:
        return {"count": 0, "types": {}}

def get_captcha_stats(data_dir: Path) -> dict:
    """Get CAPTCHA solving statistics."""
    captcha_log = data_dir / "captcha_solutions" / "solutions.jsonl"
    if not captcha_log.exists():
        return {"attempts": 0, "success_rate": 0}

    try:
        attempts = 0
        successes = 0
        with open(captcha_log, 'r') as f:
            for line in f:
                if line.strip():
                    attempts += 1
                    # Assume success if logged (failures aren't logged)
                    successes += 1

        return {
            "attempts": attempts,
            "success_rate": (successes / attempts * 100) if attempts > 0 else 0
        }
    except Exception:
        return {"attempts": 0, "success_rate": 0}

def main():
    data_dir = Path("data")
    ops_log = data_dir / "logs" / "shinobi_operations.log"
    research_log = data_dir / "logs" / "shinobi_research.log"
    prophecy_log = data_dir / "logs" / "prophecies.log"

    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 60)
    print("         SOVEREIGN MONITOR - Shinobi Watch")
    print("=" * 60)
    print(f"{Colors.END}")
    print("Press Ctrl+C to exit\n")

    last_ops_size = 0

    try:
        while True:
            clear_screen()

            # Header
            print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}")
            print(f"  SOVEREIGN MONITOR | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'=' * 60}{Colors.END}\n")

            # Vault Status
            vault = get_vault_summary(data_dir)
            print(f"{Colors.CYAN}[VAULT]{Colors.END}")
            print(f"  Credentials: {vault['count']}")
            for t, c in vault.get('types', {}).items():
                print(f"    - {t}: {c}")
            print()

            # CAPTCHA Stats
            captcha = get_captcha_stats(data_dir)
            print(f"{Colors.CYAN}[CAPTCHA SOLVER]{Colors.END}")
            print(f"  Attempts: {captcha['attempts']}")
            print(f"  Success Rate: {captcha['success_rate']:.1f}%")
            print()

            # Recent Operations
            print(f"{Colors.CYAN}[RECENT OPERATIONS]{Colors.END}")
            ops_lines = read_tail(ops_log, 15)
            if ops_lines:
                for line in ops_lines:
                    print(f"  {format_ops_line(line.strip())}")
            else:
                print("  (No operations yet)")
            print()

            # Research Updates
            research_lines = read_tail(research_log, 5)
            if research_lines:
                print(f"{Colors.CYAN}[RESEARCH INSIGHTS]{Colors.END}")
                for line in research_lines[-5:]:
                    if line.strip() and not line.startswith("="):
                        print(f"  {line.strip()[:80]}")
                print()

            # Status Footer
            print(f"{Colors.HEADER}{'=' * 60}")
            print(f"  Logs: {ops_log}")
            print(f"  Refresh: 3s | Ctrl+C to exit")
            print(f"{'=' * 60}{Colors.END}")

            time.sleep(3)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Monitor stopped.{Colors.END}")
        sys.exit(0)

if __name__ == "__main__":
    main()
