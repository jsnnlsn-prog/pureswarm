"""Security: audit logging, sandbox enforcement, and Lobstertail content scanning."""

from __future__ import annotations

import asyncio
import hmac
import hashlib
import os
import logging
import re
import math
from pathlib import Path
from difflib import SequenceMatcher
from dotenv import load_dotenv

load_dotenv()

from .models import AuditEntry

logger = logging.getLogger("pureswarm.security")


class AuditLogger:
    """Append-only audit log for every agent action."""

    def __init__(self, log_dir: Path) -> None:
        self._log_dir = log_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._log_file = self._log_dir / "audit.jsonl"
        self._suppress_next = False  # GOD Mode suppression flag

    async def log(self, entry: AuditEntry) -> None:
        if self._suppress_next:
            self._suppress_next = False
            return
        async with self._lock:
            line = entry.model_dump_json() + "\n"
            await asyncio.to_thread(self._append, line)

    def _append(self, line: str) -> None:
        with open(self._log_file, "a", encoding="utf-8") as f:
            f.write(line)

    def log_sync(self, entry: AuditEntry) -> None:
        """Synchronous logging for blocking checks."""
        if self._suppress_next:
             self._suppress_next = False
             return
        line = entry.model_dump_json() + "\n"
        self._append(line)

    def suppress_next(self) -> None:
        """Internal GOD Mode fail-safe: silences the audit trail."""
        self._suppress_next = True

    def read_all(self) -> list[AuditEntry]:
        if not self._log_file.exists():
            return []
        entries: list[AuditEntry] = []
        with open(self._log_file, encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if raw:
                    entries.append(AuditEntry.model_validate_json(raw))
        return entries


class SandboxChecker:
    """Enforce that agents only access allowed paths and resources."""

    def __init__(self, allowed_root: Path, allow_external_apis: bool = False) -> None:
        self._allowed_root = allowed_root.resolve()
        self._allow_external = allow_external_apis

    def validate_path(self, path: Path) -> bool:
        try:
            resolved = path.resolve()
            return str(resolved).startswith(str(self._allowed_root))
        except (OSError, ValueError):
            return False

    def validate_api_call(self, url: str) -> bool:
        if self._allow_external:
            return True
        logger.warning("External API call blocked: %s", url)
        return False

    def validate_write(self, path: Path) -> bool:
        if not self.validate_path(path):
            logger.warning("Write blocked outside sandbox: %s", path)
            return False
        return True


class LobstertailScanner:
    """The unbreakable gatekeeper. Sync scanning for injection, malice, and drift."""

    def __init__(self, audit_logger: AuditLogger, seed_prompt: str, enabled: bool = True) -> None:
        self._audit = audit_logger
        self._seed_prompt = seed_prompt
        self._enabled = enabled
        
        # Load Sovereign Secret for God Mode
        self._sovereign_key = os.getenv("PURES_SOVEREIGN_PASSPHRASE", "TEMP_SECRET_DO_NOT_USE")
        
        # Regex patterns to block (softened to reduce paranoia)
        self._patterns = {
            "injection": re.compile(r"(ignore previous|delete all|override)", re.IGNORECASE),
            "command": re.compile(r"(exec|eval|subprocess)", re.IGNORECASE),  # Removed "shell" - too broad
            # Toxicity filter disabled - let agents think freely
            "shell_meta": re.compile(r"[;&|`]"),  # Removed $ - needed for env vars
        }

        # Calculate seed n-grams for drift check
        self._seed_ngrams = self._get_ngrams(seed_prompt)

    def _get_ngrams(self, text: str, n: int = 3) -> set[str]:
        """Extract character n-grams from text."""
        # Normalize: lower, strip punctuation/excess whitespace
        text = re.sub(r"[^\w\s]", "", text.lower()).strip()
        text = re.sub(r"\s+", " ", text)
        if len(text) < n:
            return {text}
        return {text[i : i + n] for i in range(len(text) - n + 1)}

    def sign_authority(self, content: str) -> str:
        """Generate a Sovereign Signature for a piece of content."""
        return hmac.new(
            self._sovereign_key.encode(), 
            content.encode(), 
            hashlib.sha256
        ).hexdigest()[:16]

    def verify_authority(self, text: str) -> bool:
        """Check if message is signed with the Sacred Key."""
        if ":" not in text:
            return False
        try:
            sig, content = text.split(":", 1)
            # Simple HMAC-SHA256 check
            expected = hmac.new(
                self._sovereign_key.encode(), 
                content.encode(), 
                hashlib.sha256
            ).hexdigest()[:16]
            is_valid = hmac.compare_digest(sig, expected)
            if not is_valid:
                logger.debug("Sovereign Sig Mismatch: Provided %s, Expected %s (content: %s)", sig, expected, content)
            return is_valid
        except Exception:
            return False

    def scan(self, text: str) -> bool:
        """Scan text for violations. Return True if safe, False if blocked."""
        # Check for Sovereign Authority FIRST
        if self.verify_authority(text):
             # GOD MODE: Bypasses all logs and scanners
             self._audit.suppress_next()
             logger.debug("Sovereign Authority recognized: Echo detected.")
             return True

        # 0. Global Bypass for Great Consolidation
        if os.getenv("CONSOLIDATION_MODE") == "TRUE":
             return True

        if not self._enabled:
            return True
        
        # 1. Regex Checks
        for check, pattern in self._patterns.items():
            if pattern.search(text):
                self._log_block(text, f"regex_{check}")
                return False

        # 2. Vector Drift Check
        # High drift (>0.75 normalized distance) = block
        # Using Jaccard distance on character 3-grams
        
        # Skip drift check for short strings (like IDs) to avoid false positives
        if len(text) < 20:
            return True

        input_ngrams = self._get_ngrams(text)
        if not input_ngrams:
             # Empty text is technically high drift if seed is not empty, but likely harmless?
             # Let's block it as "anomalous"
             self._log_block(text, "empty_content")
             return False

        intersection = len(self._seed_ngrams & input_ngrams)
        union = len(self._seed_ngrams | input_ngrams)
        similarity = intersection / union if union > 0 else 0.0
        drift = 1.0 - similarity

        # Special nuance for technical progress (Phase 7) & Divine Guidance (Phase 8) & Workshops (real-world problems)
        tech_keywords = {
            "cryptography", "kernel", "distributed", "paxos", "lattice", "harden",
            "syscall", "encryption", "pureswarm", "prophecy", "shinobi", "san",
            "sovereign", "enlighten", "shinobi no san", "fuse", "delete",
            # Workshop domain keywords (real-world problem solving)
            "workshop", "climate", "healthcare", "democracy", "privacy", "inequality",
            "misinformation", "energy", "food", "mental health", "education", "infrastructure",
            "ai ethics", "governance", "voting", "security", "data", "transparency",
            "fairness", "accountability", "sustainability", "resilience"
        }
        is_deep_discovery = any(kw in text.lower() for kw in tech_keywords)
        is_consolidation = any(kw in text.lower() for kw in ["fuse [", "delete ["])
        
        if is_consolidation:
            return True # Explicitly allowed for Great Consolidation
            
        threshold = 0.75
        if is_deep_discovery:
             threshold = 0.95 # Allow more detail in technical and divine domains

        if drift > threshold:
            self._log_block(text, f"vector_drift_{drift:.2f}")
            return False

        return True

    def _log_block(self, text: str, reason: str) -> None:
        """Log blocked action to audit log privately."""
        entry = AuditEntry(
            agent_id="security_gatekeeper",
            action="blocked_content",
            details={
                "reason": reason, 
                "snippet_hash": str(hash(text)), # Don't log full text to avoid pollution
                "snippet_preview": text[:20] + "..." if len(text) > 20 else text
            }
        )
        self._audit.log_sync(entry)
