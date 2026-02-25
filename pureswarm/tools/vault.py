"""Credential Vault - Shinobi's keys, Sovereign's override.

SECURITY MODEL:
- Shinobi agents use credentials day-to-day
- Sovereign (Jay) has FULL READ ACCESS at all times
- All credential access is logged
- Emergency lockout capability
- Human-readable backup for "break glass" scenarios
"""

from __future__ import annotations

import json
import logging
import os
import hashlib
import base64
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger("pureswarm.tools.vault")


@dataclass
class Credential:
    """A stored credential."""
    name: str                    # e.g., "shinobi_email", "upwork_account"
    credential_type: str         # "email", "platform", "api_key"
    username: str
    password: str
    email: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = ""
    last_used: Optional[str] = None
    created_by: str = "shinobi"  # Track who created it


class SovereignVault:
    """Secure credential storage with Sovereign override access.

    The vault encrypts credentials but ALSO maintains a sovereign-readable
    backup that Jay can access directly in emergencies.
    """

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._vault_dir = data_dir / "vault"
        self._vault_dir.mkdir(parents=True, exist_ok=True)

        # Encrypted vault file (for programmatic access)
        self._vault_file = self._vault_dir / "credentials.vault"

        # SOVEREIGN OVERRIDE: Human-readable backup
        # This file is for YOU, Jay - plain JSON, always accessible
        self._sovereign_backup = self._vault_dir / "SOVEREIGN_ACCESS.json"

        # Access log - every credential read/write is tracked
        self._access_log = self._vault_dir / "access_log.jsonl"

        # Lockout flag - if True, all credential access is denied
        self._lockout_file = self._vault_dir / ".lockout"

        # Initialize encryption key from Sovereign passphrase
        self._passphrase = os.getenv("PURES_SOVEREIGN_PASSPHRASE", "FALLBACK_KEY")
        self._fernet = self._init_encryption()

        # Load existing credentials
        self._credentials: Dict[str, Credential] = {}
        self._load_vault()

    def _init_encryption(self) -> Fernet:
        """Derive encryption key from Sovereign passphrase."""
        salt = b"pureswarm_shinobi_vault_v1"  # Static salt (passphrase provides entropy)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._passphrase.encode()))
        return Fernet(key)

    def _load_vault(self) -> None:
        """Load credentials from encrypted vault."""
        if not self._vault_file.exists():
            return

        try:
            encrypted = self._vault_file.read_bytes()
            decrypted = self._fernet.decrypt(encrypted)
            data = json.loads(decrypted.decode())

            for name, cred_data in data.items():
                self._credentials[name] = Credential(**cred_data)

            logger.debug("Vault loaded: %d credentials", len(self._credentials))
        except Exception as e:
            logger.error("Failed to load vault: %s", e)

    def _save_vault(self) -> None:
        """Save credentials to encrypted vault AND sovereign backup."""
        # Prepare data
        data = {name: asdict(cred) for name, cred in self._credentials.items()}

        # 1. Save encrypted vault
        try:
            encrypted = self._fernet.encrypt(json.dumps(data).encode())
            self._vault_file.write_bytes(encrypted)
        except Exception as e:
            logger.error("Failed to save encrypted vault: %s", e)

        # 2. SOVEREIGN BACKUP - Human readable, always accessible
        try:
            backup_data = {
                "_NOTICE": "SOVEREIGN EMERGENCY ACCESS - All Shinobi credentials",
                "_UPDATED": datetime.now(timezone.utc).isoformat(),
                "_INSTRUCTIONS": "These are Shinobi's credentials. Use for emergency override.",
                "credentials": data
            }
            self._sovereign_backup.write_text(
                json.dumps(backup_data, indent=2),
                encoding="utf-8"
            )
            logger.debug("Sovereign backup updated")
        except Exception as e:
            logger.error("Failed to save sovereign backup: %s", e)

    def _log_access(self, action: str, credential_name: str, accessor: str) -> None:
        """Log all credential access for audit."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "credential": credential_name,
            "accessor": accessor
        }
        with open(self._access_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def is_locked(self) -> bool:
        """Check if vault is in lockout mode."""
        return self._lockout_file.exists()

    def lockout(self, reason: str = "Emergency lockout") -> None:
        """EMERGENCY: Lock all credential access immediately."""
        self._lockout_file.write_text(
            json.dumps({
                "locked_at": datetime.now(timezone.utc).isoformat(),
                "reason": reason
            }),
            encoding="utf-8"
        )
        logger.critical("VAULT LOCKOUT ACTIVATED: %s", reason)
        self._log_access("LOCKOUT", "*", "sovereign")

    def unlock(self) -> None:
        """Remove lockout (Sovereign only)."""
        if self._lockout_file.exists():
            self._lockout_file.unlink()
            logger.info("Vault lockout removed")
            self._log_access("UNLOCK", "*", "sovereign")

    def store(self,
              name: str,
              credential_type: str,
              username: str,
              password: str,
              email: Optional[str] = None,
              url: Optional[str] = None,
              notes: Optional[str] = None,
              created_by: str = "shinobi") -> bool:
        """Store a new credential."""
        if self.is_locked():
            logger.warning("Vault is locked - cannot store credentials")
            return False

        cred = Credential(
            name=name,
            credential_type=credential_type,
            username=username,
            password=password,
            email=email,
            url=url,
            notes=notes,
            created_at=datetime.now(timezone.utc).isoformat(),
            created_by=created_by
        )

        self._credentials[name] = cred
        self._save_vault()
        self._log_access("STORE", name, created_by)

        logger.info("Credential stored: %s (type=%s)", name, credential_type)
        return True

    def get(self, name: str, accessor: str = "shinobi") -> Optional[Credential]:
        """Retrieve a credential."""
        if self.is_locked():
            logger.warning("Vault is locked - access denied")
            return None

        cred = self._credentials.get(name)
        if cred:
            # Update last used
            cred.last_used = datetime.now(timezone.utc).isoformat()
            self._save_vault()
            self._log_access("GET", name, accessor)

        return cred

    def list_credentials(self) -> List[Dict[str, str]]:
        """List all stored credentials (names and types only, no secrets)."""
        return [
            {
                "name": cred.name,
                "type": cred.credential_type,
                "username": cred.username,
                "email": cred.email or "",
                "created_at": cred.created_at
            }
            for cred in self._credentials.values()
        ]

    def delete(self, name: str, accessor: str = "sovereign") -> bool:
        """Delete a credential (Sovereign recommended)."""
        if name in self._credentials:
            del self._credentials[name]
            self._save_vault()
            self._log_access("DELETE", name, accessor)
            logger.info("Credential deleted: %s", name)
            return True
        return False

    def export_for_sovereign(self) -> str:
        """Export all credentials as readable text for Sovereign."""
        lines = [
            "=" * 60,
            "SOVEREIGN CREDENTIAL EXPORT",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            "=" * 60,
            ""
        ]

        for cred in self._credentials.values():
            lines.extend([
                f"[{cred.name}]",
                f"  Type: {cred.credential_type}",
                f"  Username: {cred.username}",
                f"  Password: {cred.password}",
                f"  Email: {cred.email or 'N/A'}",
                f"  URL: {cred.url or 'N/A'}",
                f"  Notes: {cred.notes or 'N/A'}",
                f"  Created: {cred.created_at}",
                f"  Created By: {cred.created_by}",
                ""
            ])

        return "\n".join(lines)

    def get_access_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent access log entries."""
        if not self._access_log.exists():
            return []

        entries = []
        with open(self._access_log, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        return entries[-limit:]


# Convenience functions for quick Sovereign access
def quick_lockout(data_dir: Path = Path("data")) -> None:
    """Emergency lockout - run this if things go wrong."""
    vault = SovereignVault(data_dir)
    vault.lockout("Manual emergency lockout")
    print("LOCKOUT ACTIVATED - All Shinobi credential access blocked")


def quick_export(data_dir: Path = Path("data")) -> str:
    """Export all credentials for Sovereign review."""
    vault = SovereignVault(data_dir)
    return vault.export_for_sovereign()


def quick_unlock(data_dir: Path = Path("data")) -> None:
    """Remove lockout."""
    vault = SovereignVault(data_dir)
    vault.unlock()
    print("Vault unlocked")
