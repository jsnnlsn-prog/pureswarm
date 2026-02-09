"""Execution Manager: Bridges consensus-adopted actions to real-world effects."""

from __future__ import annotations

import logging
from pathlib import Path
from .models import Tenet

logger = logging.getLogger("pureswarm.execution")

class ExecutionManager:
    """Manages the execution of actions adopted by the swarm."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._execution_root = data_dir / "execution"
        self._execution_root.mkdir(parents=True, exist_ok=True)
        self._history: list[str] = []

    async def execute_tenet(self, tenet: Tenet) -> bool:
        """Analyze a tenet for execution triggers and perform associated actions."""
        text = tenet.text.upper()
        
        # Look for ACTION: or EXECUTE: prefixes
        if "ACTION:" in text or "EXECUTE:" in text:
            try:
                # Extract the command
                marker = "ACTION:" if "ACTION:" in text else "EXECUTE:"
                command = tenet.text.split(marker, 1)[1].strip()
                
                logger.info("Execution Triggered: %s", command)
                
                # Implementation for Project Deep Guard (Security Rules)
                if "SECURITY RULE" in command.upper():
                    rule_id = tenet.id
                    rule_path = self._execution_root / f"rule_{rule_id}.json"
                    rule_content = {
                        "rule_id": rule_id,
                        "description": command,
                        "origin_tenet": tenet.id,
                        "status": "deployed"
                    }
                    import json
                    rule_path.write_text(json.dumps(rule_content, indent=2), encoding="utf-8")
                    logger.info("Security Rule Deployed: %s", rule_path)
                
                self._history.append(command)
                return True
            except Exception as e:
                logger.error("Execution failed for tenet %s: %s", tenet.id, e)
                return False
        
        return False

    def get_execution_history(self) -> list[str]:
        return self._history
