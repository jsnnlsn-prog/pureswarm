"""Mission Executor - Turns prophecies into action.

When Shinobi no San receives an EXTERNAL prophecy, this module
parses the mission and executes the real-world operations.
"""

from __future__ import annotations

import asyncio
import logging
import random
import string
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger("pureswarm.tools.mission")


class MissionExecutor:
    """Executes external missions for Shinobi no San.

    Turns prophecy directives into real browser/email/platform actions.
    """

    def __init__(self, agent_id: str, data_dir: Path = None) -> None:
        self._agent_id = agent_id
        self._data_dir = data_dir or Path("data")
        self._ops_log = self._data_dir / "logs" / "shinobi_operations.log"
        self._ops_log.parent.mkdir(parents=True, exist_ok=True)

    def _log_operation(self, operation: str, details: str, status: str = "EXECUTING") -> None:
        """Log operation to Shinobi operations log."""
        timestamp = datetime.now().isoformat()
        with open(self._ops_log, "a", encoding="utf-8") as f:
            f.write(f"\n[{timestamp}] [{status}] Agent {self._agent_id}\n")
            f.write(f"  Operation: {operation}\n")
            f.write(f"  Details: {details}\n")

    def _generate_secure_password(self, length: int = 16) -> str:
        """Generate a secure password."""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.SystemRandom().choice(chars) for _ in range(length))

    def _generate_username(self, base: str = "Dopamine_Ronin") -> str:
        """Generate a unique username variant."""
        suffix = ''.join(random.choices(string.digits, k=4))
        variants = [
            f"Dopamine_Ronin{suffix}",
            f"DopamineRonin{suffix}",
            f"Dopamine_Ronin_{suffix}",
            f"dopamine_ronin{suffix}",
            f"DopamineRonin_AI{suffix}",
        ]
        return random.choice(variants)

    async def execute_mission(self, mission_text: str) -> Dict[str, Any]:
        """Parse and execute a mission from prophecy content.

        This is the main entry point - it reads the mission,
        loads instruction files, and executes the steps.
        """
        self._log_operation("MISSION_START", f"Received mission directive")

        result = {
            "success": False,
            "operations_completed": [],
            "errors": [],
            "credentials_created": [],
        }

        try:
            # Import here to avoid circular imports
            from .internet import InternetAccess

            # Create internet access for this agent
            internet = InternetAccess(self._agent_id, is_triad=True, data_dir=self._data_dir)

            # Read instruction files
            instructions_dir = self._data_dir / "instructions"
            profile_data = self._load_profile_data(instructions_dir)

            self._log_operation("INSTRUCTIONS_LOADED", f"Loaded profile data for: {profile_data.get('name', 'Jay Nelson')}")

            # PHASE 1: Create operational email
            self._log_operation("PHASE_1", "Creating operational email account")

            email_result = await self._create_operational_email(internet, profile_data)
            if email_result.get("success"):
                result["operations_completed"].append("email_created")
                result["credentials_created"].append(email_result.get("email"))
                operational_email = email_result.get("email")
                operational_password = email_result.get("password")
                self._log_operation("EMAIL_CREATED", f"Created: {operational_email}", "SUCCESS")
            else:
                result["errors"].append(f"Email creation failed: {email_result.get('error')}")
                self._log_operation("EMAIL_FAILED", email_result.get("error", "Unknown"), "FAILED")
                # Can't proceed without email
                return result

            # PHASE 2: Register on platforms
            self._log_operation("PHASE_2", "Registering on gig platforms")

            platforms = ["upwork", "fiverr"]  # Start with priority platforms
            for platform in platforms:
                self._log_operation(f"PLATFORM_{platform.upper()}", f"Attempting registration")

                platform_result = await self._register_platform(
                    internet, platform, operational_email, operational_password, profile_data
                )

                if platform_result.get("success"):
                    result["operations_completed"].append(f"{platform}_registered")
                    self._log_operation(f"PLATFORM_{platform.upper()}", "Registration complete", "SUCCESS")
                else:
                    result["errors"].append(f"{platform} registration failed: {platform_result.get('error')}")
                    self._log_operation(f"PLATFORM_{platform.upper()}", platform_result.get("error", "Unknown"), "FAILED")

                # Human-like delay between platforms
                await asyncio.sleep(random.uniform(30, 60))

            # PHASE 3: Mission complete
            result["success"] = len(result["operations_completed"]) > 0

            if result["success"]:
                self._log_operation("MISSION_COMPLETE", f"Completed {len(result['operations_completed'])} operations", "SUCCESS")
            else:
                self._log_operation("MISSION_FAILED", f"No operations completed", "FAILED")

            # Cleanup
            await internet.cleanup()

        except Exception as e:
            result["errors"].append(str(e))
            self._log_operation("MISSION_ERROR", str(e), "ERROR")
            logger.exception("Mission execution failed")

        return result

    def _load_profile_data(self, instructions_dir: Path) -> Dict[str, Any]:
        """Load profile data from instruction files."""
        profile = {
            "name": "Jay Nelson",
            "first_name": "Jay",
            "last_name": "Nelson",
            "headline": "Elite Web Scraping & AI Automation | I Handle Sites That Block Everyone Else",
            "hourly_rate": "$95",
            "skills": [
                "Web Scraping", "Python", "Data Mining", "API Integration",
                "Automation", "Selenium", "BeautifulSoup", "AI/ML"
            ],
        }

        # Try to load from master profile
        master_profile = instructions_dir / "GIG_PLATFORMS_MASTER_PROFILE.md"
        if master_profile.exists():
            try:
                content = master_profile.read_text(encoding="utf-8")
                # Parse some key info (simple extraction)
                if "Jay Nelson" in content:
                    profile["name"] = "Jay Nelson"
                if "$95" in content:
                    profile["hourly_rate"] = "$95"
            except Exception:
                pass

        return profile

    async def _create_operational_email(self, internet, profile_data: Dict) -> Dict[str, Any]:
        """Create the operational email account."""
        username = self._generate_username()
        password = self._generate_secure_password()

        # Try ProtonMail first (more privacy-focused)
        result = await internet.create_email_account(
            provider="protonmail",
            first_name=profile_data.get("first_name", "Jay"),
            last_name=profile_data.get("last_name", "Nelson"),
            desired_username=username,
            password=password
        )

        if result.success:
            return {
                "success": True,
                "email": result.data.get("email", f"{username}@proton.me"),
                "password": password,
                "provider": "protonmail"
            }

        # Fallback to Gmail
        result = await internet.create_email_account(
            provider="gmail",
            first_name=profile_data.get("first_name", "Jay"),
            last_name=profile_data.get("last_name", "Nelson"),
            desired_username=username,
            password=password
        )

        if result.success:
            return {
                "success": True,
                "email": result.data.get("email", f"{username}@gmail.com"),
                "password": password,
                "provider": "gmail"
            }

        return {"success": False, "error": result.error or "Email creation failed"}

    async def _register_platform(self, internet, platform: str, email: str, password: str, profile_data: Dict) -> Dict[str, Any]:
        """Register on a freelance platform."""
        result = await internet.register_platform(
            platform=platform,
            email=email,
            password=password,
            first_name=profile_data.get("first_name", "Jay"),
            last_name=profile_data.get("last_name", "Nelson"),
            username=self._generate_username()
        )

        if result.success:
            return {"success": True, "platform": platform}

        return {"success": False, "error": result.error or f"{platform} registration failed"}


async def execute_external_mission(agent_id: str, mission_text: str, data_dir: Path = None) -> Dict[str, Any]:
    """Convenience function to execute a mission.

    Called from agent.py when an EXTERNAL prophecy is received.
    """
    executor = MissionExecutor(agent_id, data_dir)
    return await executor.execute_mission(mission_text)
