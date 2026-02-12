"""Prophecy Engine: Direct authenticated channel for Sovereign directives to the Triad."""

from __future__ import annotations

import hmac
import hashlib
import logging
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger("pureswarm.prophecy")

class Prophecy(BaseModel):
    """A direct directive from the Sovereign."""
    content: str
    signature: str
    target_triad: bool = True

class ProphecyEngine:
    """Manages the reception and validation of Prophesies."""

    def __init__(self, sovereign_key: str) -> None:
        self._sovereign_key = sovereign_key
        self._history: List[Prophecy] = []

    def verify_and_capture(self, content: str, signature: str) -> bool:
        """Verify a signature and store the prophecy if valid."""
        try:
            expected = hmac.new(
                self._sovereign_key.encode(),
                content.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            if hmac.compare_digest(signature, expected):
                prophecy = Prophecy(content=content, signature=signature)
                self._history.append(prophecy)
                logger.info("Prophecy Received and Authenticated: %s", content[:50])
                return True
            else:
                logger.warning("Invalid Prophecy Signature Attempted")
                return False
        except Exception as e:
            logger.error("Error verifying prophecy: %s", e)
            return False

    def load_from_file(self, file_path: str = "data/.prophecy") -> bool:
        """Attempt to load a prophecy from a file."""
        import os
        from pathlib import Path
        
        path = Path(file_path)
        if not path.exists():
            return False
            
        try:
            content = path.read_text(encoding="utf-8").strip()
            if not content:
                return False
                
            # Expected format: SIGNATURE:CONTENT
            if ":" not in content:
                logger.warning("Invalid prophecy file format")
                return False
                
            sig, text = content.split(":", 1)
            if self.verify_and_capture(text, sig):
                # Consume file after successful read
                # path.unlink() # verifying first, maybe don't delete yet?
                return True
            return False
        except Exception as e:
            logger.error("Failed to load prophecy from file: %s", e)
            return False

    def get_latest_prophecy(self) -> Optional[Prophecy]:
        """Retrieve the most recent verified prophecy."""
        # Always check for new prophecy file
        self.load_from_file()
        return self._history[-1] if self._history else None
