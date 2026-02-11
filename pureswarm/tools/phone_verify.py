"""VoIP Phone Verification - Programmatic phone number acquisition and SMS receipt.

NO human services. 100% API-driven.

Supported providers:
- Twilio (most reliable, requires account)
- TextNow API (free tier available)
- Virtual number APIs
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger("pureswarm.tools.phone_verify")


@dataclass
class PhoneNumber:
    """A virtual phone number for verification."""
    number: str
    provider: str
    country: str = "US"
    capabilities: List[str] = None  # ["sms", "voice"]
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = ["sms"]


@dataclass
class VerificationCode:
    """A received verification code."""
    code: str
    from_number: str
    message: str
    received_at: datetime
    platform: str = ""  # e.g., "google", "upwork"


class TwilioProvider:
    """Twilio-based phone verification.

    Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER env vars.
    """

    def __init__(self) -> None:
        self._account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self._auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self._phone_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        self._client = None

    def is_configured(self) -> bool:
        return bool(self._account_sid and self._auth_token)

    async def initialize(self) -> bool:
        """Initialize Twilio client."""
        if not self.is_configured():
            logger.warning("Twilio not configured - missing credentials")
            return False

        try:
            from twilio.rest import Client
            self._client = Client(self._account_sid, self._auth_token)
            logger.info("Twilio client initialized")
            return True
        except ImportError:
            logger.error("Twilio library not installed. Run: pip install twilio")
            return False
        except Exception as e:
            logger.error("Twilio initialization failed: %s", e)
            return False

    async def get_phone_number(self) -> Optional[PhoneNumber]:
        """Get a phone number for verification.

        Uses existing Twilio number or purchases a new one.
        """
        if not self._client:
            await self.initialize()

        if not self._client:
            return None

        try:
            # Use existing number if configured
            if self._phone_number:
                return PhoneNumber(
                    number=self._phone_number,
                    provider="twilio",
                    capabilities=["sms", "voice"]
                )

            # Otherwise, search for available numbers
            available = self._client.available_phone_numbers("US").local.list(
                sms_enabled=True,
                limit=1
            )

            if available:
                # Purchase the number
                purchased = self._client.incoming_phone_numbers.create(
                    phone_number=available[0].phone_number
                )
                logger.info("Purchased Twilio number: %s", purchased.phone_number)
                return PhoneNumber(
                    number=purchased.phone_number,
                    provider="twilio",
                    capabilities=["sms", "voice"]
                )

        except Exception as e:
            logger.error("Failed to get Twilio number: %s", e)

        return None

    async def wait_for_code(self, phone_number: str, timeout: int = 120,
                           platform_hint: str = "") -> Optional[VerificationCode]:
        """Wait for a verification code to arrive via SMS.

        Args:
            phone_number: The phone number to check
            timeout: Max seconds to wait
            platform_hint: Hint about expected sender (e.g., "google", "upwork")

        Returns:
            VerificationCode if received, None if timeout
        """
        if not self._client:
            return None

        start_time = datetime.now()
        check_interval = 5  # Check every 5 seconds

        # Get messages received after start time
        while (datetime.now() - start_time).seconds < timeout:
            try:
                messages = self._client.messages.list(
                    to=phone_number,
                    limit=10
                )

                for msg in messages:
                    # Check if message is recent (within last 2 minutes)
                    if msg.date_sent and msg.date_sent > start_time - timedelta(minutes=2):
                        # Extract verification code from message
                        code = self._extract_code(msg.body, platform_hint)
                        if code:
                            logger.info("Verification code received: %s", code)
                            return VerificationCode(
                                code=code,
                                from_number=msg.from_,
                                message=msg.body,
                                received_at=msg.date_sent,
                                platform=platform_hint
                            )

            except Exception as e:
                logger.warning("Error checking messages: %s", e)

            await asyncio.sleep(check_interval)

        logger.warning("Timeout waiting for verification code")
        return None

    def _extract_code(self, message: str, platform_hint: str = "") -> Optional[str]:
        """Extract verification code from SMS message."""
        # Common patterns for verification codes
        patterns = [
            r'\b(\d{6})\b',  # 6 digits
            r'\b(\d{4})\b',  # 4 digits
            r'code[:\s]+(\d{4,6})',  # "code: 123456"
            r'verification[:\s]+(\d{4,6})',  # "verification: 123456"
            r'G-(\d{6})',  # Google format "G-123456"
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)

        return None


class VirtualNumberProvider:
    """Generic virtual number provider using various APIs.

    Supports multiple services via API.
    """

    def __init__(self, data_dir: Path = None) -> None:
        self._data_dir = data_dir or Path("data")
        self._numbers_cache = self._data_dir / "phone_numbers.json"

    async def get_free_number(self) -> Optional[PhoneNumber]:
        """Get a free virtual number from available services.

        This uses free-tier services that don't require payment.
        Note: Free numbers are often flagged by platforms.
        """
        # Try TextNow API if available
        textnow_number = await self._try_textnow()
        if textnow_number:
            return textnow_number

        # Could add more free providers here

        return None

    async def _try_textnow(self) -> Optional[PhoneNumber]:
        """Try to get a TextNow number."""
        # TextNow requires their app/web interface
        # This would need browser automation to get a number
        # For now, return None - implement if needed
        return None


class RealSIMProvider:
    """Use a real SIM card with SMS forwarding.

    Set up:
    1. Install "SMS Forwarder" app on Android phone with SIM
    2. Configure it to POST SMS to: http://your-server:5555/sms
    3. Set REAL_PHONE_NUMBER env var to your phone number

    The incoming SMS is written to a file that this provider polls.
    """

    def __init__(self, data_dir: Path = None) -> None:
        self._data_dir = data_dir or Path("data")
        self._sms_inbox = self._data_dir / "sms_inbox"
        self._sms_inbox.mkdir(parents=True, exist_ok=True)
        self._phone_number = os.getenv("REAL_PHONE_NUMBER", "")

    def is_configured(self) -> bool:
        return bool(self._phone_number)

    async def get_phone_number(self) -> Optional[PhoneNumber]:
        """Return the configured real phone number."""
        if not self._phone_number:
            return None

        return PhoneNumber(
            number=self._phone_number,
            provider="real_sim",
            capabilities=["sms", "voice"]
        )

    async def wait_for_code(self, timeout: int = 120, platform_hint: str = "") -> Optional[VerificationCode]:
        """Wait for verification code - checks inbox OR prompts for manual entry.

        Priority:
        1. Check data/sms_inbox/ for forwarded SMS (if configured)
        2. Check data/sms_inbox/manual_code.txt for manually entered code
        3. Alert user and wait for manual input
        """
        start_time = datetime.now()
        check_interval = 3  # Check every 3 seconds
        manual_code_file = self._sms_inbox / "manual_code.txt"

        # ALERT THE SOVEREIGN
        alert_msg = f"""
╔══════════════════════════════════════════════════════════════╗
║  🔔 VERIFICATION CODE NEEDED - {platform_hint.upper()}
║
║  Phone: {self._phone_number}
║
║  When you receive the code, either:
║  1. Enter it in: {manual_code_file}
║  2. Or type it when prompted
║
║  Waiting {timeout} seconds...
╚══════════════════════════════════════════════════════════════╝
"""
        print(alert_msg)
        logger.info("VERIFICATION CODE NEEDED for %s on %s", platform_hint, self._phone_number)

        # Write alert to file for monitor.py to pick up
        alert_file = self._sms_inbox / "AWAITING_CODE.txt"
        with open(alert_file, 'w') as f:
            f.write(f"Platform: {platform_hint}\nPhone: {self._phone_number}\nTime: {datetime.now().isoformat()}\n")

        while (datetime.now() - start_time).seconds < timeout:
            # Check 1: Manual code file
            if manual_code_file.exists():
                try:
                    code = manual_code_file.read_text().strip()
                    if code and len(code) >= 4:
                        logger.info("Found manual code: %s", code)
                        manual_code_file.unlink()  # Delete after reading
                        if alert_file.exists():
                            alert_file.unlink()
                        return VerificationCode(
                            code=code,
                            from_number="manual",
                            message="Manually entered",
                            received_at=datetime.now(),
                            platform=platform_hint
                        )
                except Exception as e:
                    logger.warning("Error reading manual code: %s", e)

            # Check 2: SMS inbox files (if forwarding is set up)
            sms_files = sorted(self._sms_inbox.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

            for sms_file in sms_files[:5]:  # Check 5 most recent
                try:
                    with open(sms_file, 'r') as f:
                        sms_data = json.loads(f.read())

                    # Check if this SMS arrived after we started waiting
                    sms_time = datetime.fromisoformat(sms_data.get("timestamp", "2000-01-01"))
                    if sms_time > start_time - timedelta(minutes=1):
                        message = sms_data.get("body", "")
                        code = self._extract_code(message, platform_hint)

                        if code:
                            logger.info("Found verification code in SMS: %s", code)

                            # Mark as processed
                            processed_file = sms_file.with_suffix(".processed")
                            sms_file.rename(processed_file)
                            if alert_file.exists():
                                alert_file.unlink()

                            return VerificationCode(
                                code=code,
                                from_number=sms_data.get("from", "unknown"),
                                message=message,
                                received_at=sms_time,
                                platform=platform_hint
                            )

                except Exception as e:
                    logger.warning("Error reading SMS file %s: %s", sms_file, e)

            await asyncio.sleep(check_interval)

        # Cleanup
        if alert_file.exists():
            alert_file.unlink()

        logger.warning("Timeout waiting for SMS verification code")
        return None

    def _extract_code(self, message: str, platform_hint: str = "") -> Optional[str]:
        """Extract verification code from SMS message."""
        patterns = [
            r'G-(\d{6})',  # Google format "G-123456"
            r'code[:\s]+(\d{4,6})',  # "code: 123456"
            r'verification[:\s]+(\d{4,6})',
            r'\b(\d{6})\b',  # 6 digits
            r'\b(\d{4})\b',  # 4 digits
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)

        return None


# Simple webhook receiver for SMS forwarding
# Run this separately or integrate with your server:
#
# from flask import Flask, request
# app = Flask(__name__)
#
# @app.route('/sms', methods=['POST'])
# def receive_sms():
#     data = request.json
#     sms_file = Path(f"data/sms_inbox/{datetime.now().isoformat()}.json")
#     sms_file.write_text(json.dumps({
#         "from": data.get("from", ""),
#         "body": data.get("body", ""),
#         "timestamp": datetime.now().isoformat()
#     }))
#     return "OK"
#
# app.run(host='0.0.0.0', port=5555)


class PhoneVerificationService:
    """Main service for phone verification.

    Combines multiple providers for reliability.
    Priority order:
    1. Real SIM (best reputation, set REAL_PHONE_NUMBER env var)
    2. Twilio (reliable, requires account)
    3. Free virtual providers (often flagged)
    """

    def __init__(self, data_dir: Path = None) -> None:
        self._data_dir = data_dir or Path("data")
        self._real_sim = RealSIMProvider(data_dir)
        self._twilio = TwilioProvider()
        self._virtual = VirtualNumberProvider(data_dir)
        self._active_number: Optional[PhoneNumber] = None
        self._active_provider: str = ""
        self._verification_log = self._data_dir / "phone_verifications.jsonl"

    async def initialize(self) -> bool:
        """Initialize the phone verification service."""
        # Real SIM is always ready if configured
        if self._real_sim.is_configured():
            logger.info("Real SIM provider configured - best reputation!")
            return True

        # Try Twilio
        if self._twilio.is_configured():
            return await self._twilio.initialize()

        logger.warning("No phone provider configured. Set REAL_PHONE_NUMBER or TWILIO_* env vars.")
        return False

    async def get_number(self) -> Optional[PhoneNumber]:
        """Get a phone number for verification."""
        # Priority 1: Real SIM (best carrier reputation)
        if self._real_sim.is_configured():
            number = await self._real_sim.get_phone_number()
            if number:
                self._active_number = number
                self._active_provider = "real_sim"
                logger.info("Using real SIM number: %s", number.number)
                return number

        # Priority 2: Twilio
        if self._twilio.is_configured():
            number = await self._twilio.get_phone_number()
            if number:
                self._active_number = number
                self._active_provider = "twilio"
                return number

        # Priority 3: Free providers (last resort)
        number = await self._virtual.get_free_number()
        if number:
            self._active_number = number
            self._active_provider = "virtual"
            return number

        logger.error("No phone verification provider available")
        return None

    async def request_verification(self, platform: str, phone_field_value: str = None) -> Optional[str]:
        """Get or confirm a phone number for verification.

        Args:
            platform: The platform requesting verification (e.g., "google", "upwork")
            phone_field_value: Value to enter in phone field (uses active number if None)

        Returns:
            Phone number string to enter in the form
        """
        if not self._active_number:
            number = await self.get_number()
            if not number:
                return None

        # Log the verification request
        self._log_verification(platform, "requested")

        return self._active_number.number

    async def wait_for_code(self, platform: str, timeout: int = 120) -> Optional[str]:
        """Wait for verification code to arrive.

        Args:
            platform: The platform that sent the code
            timeout: Max seconds to wait

        Returns:
            The verification code string, or None if timeout
        """
        if not self._active_number:
            logger.error("No active phone number")
            return None

        result = None

        # Use appropriate provider to wait for code
        if self._active_provider == "real_sim":
            result = await self._real_sim.wait_for_code(
                timeout=timeout,
                platform_hint=platform
            )
        elif self._active_provider == "twilio":
            result = await self._twilio.wait_for_code(
                self._active_number.number,
                timeout=timeout,
                platform_hint=platform
            )

        if result:
            self._log_verification(platform, "received", result.code)
            return result.code

        return None

    def _log_verification(self, platform: str, status: str, code: str = "") -> None:
        """Log verification events."""
        import json
        entry = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "status": status,
            "phone": self._active_number.number if self._active_number else "",
            "code": code
        }
        self._verification_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self._verification_log, "a") as f:
            f.write(json.dumps(entry) + "\n")


# Convenience function for browser integration
async def create_phone_service(data_dir: Path = None) -> PhoneVerificationService:
    """Create and initialize phone verification service."""
    service = PhoneVerificationService(data_dir)
    await service.initialize()
    return service
