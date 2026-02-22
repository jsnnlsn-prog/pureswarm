"""Shinobi's Gateway to the Outside World.

This module provides the unified interface for all external operations:
- Browser automation (account creation, platform navigation)
- HTTP API calls
- Email communication
- Credential management

All access is gated by Triad membership and logged for Sovereign oversight.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .vault import SovereignVault, Credential
from .browser import BrowserAutomation, EmailCreator, PlatformRegistrar, set_phone_service
from .http_client import ShinobiHTTPClient, VeniceAIClient, AnthropicClient, FallbackLLMClient
from .email_client import ShinobiEmailClient, EmailConfig, EMAIL_PROVIDERS, EmailTemplates
from .captcha_solver import VisionCaptchaSolver, AudioCaptchaSolver, BrowserCaptchaIntegration, create_captcha_solver
from .phone_verify import PhoneVerificationService, create_phone_service

logger = logging.getLogger("pureswarm.tools.internet")


@dataclass
class TaskResult:
    """Result of an external task."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class InternetAccess:
    """Shinobi's hands in the digital world.

    This is the main interface agents use for all external operations.
    Only Triad members (Shinobi no San) can use these capabilities.
    """

    def __init__(self, agent_id: str, is_triad: bool, data_dir: Path = None) -> None:
        self._agent_id = agent_id
        self._is_triad = is_triad
        self._data_dir = data_dir or Path("data")

        # Core tools available to all
        self._vault = SovereignVault(self._data_dir)
        self._http = ShinobiHTTPClient(self._data_dir)

        # LLM for intelligent reasoning - Anthropic primary, Venice fallback
        venice_key = os.getenv("VENICE_API_KEY", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

        venice_client = VeniceAIClient(venice_key, self._http) if venice_key else None
        anthropic_client = AnthropicClient(anthropic_key, self._http) if anthropic_key else None

        if venice_client or anthropic_client:
            self._venice = FallbackLLMClient(venice_client, anthropic_client)
            providers = []
            if anthropic_client:
                providers.append("Anthropic")
            if venice_client:
                providers.append("Venice")
            logger.info("LLM fallback chain: %s", " -> ".join(providers))
        else:
            self._venice = None

        # Only initialize advanced tools for Triad members
        if is_triad:
            self._browser: Optional[BrowserAutomation] = None
            self._email_client: Optional[ShinobiEmailClient] = None

            if venice_key:
                # AI-powered CAPTCHA solving - NO human services
                self._captcha_solver = VisionCaptchaSolver(venice_key, self._http, self._data_dir)
                self._audio_solver = AudioCaptchaSolver(venice_key, self._http)
                self._captcha_integrator = BrowserCaptchaIntegration(self._captcha_solver, self._audio_solver)
            else:
                self._captcha_solver = None
                self._audio_solver = None
                self._captcha_integrator = None

            # Phone verification (Real SIM preferred, Twilio fallback)
            self._phone_service = PhoneVerificationService(self._data_dir)
        else:
            self._browser = None
            self._email_client = None
            self._captcha_solver = None
            self._audio_solver = None
            self._captcha_integrator = None
            self._phone_service = None

    def _check_access(self) -> bool:
        """Verify Triad membership before any operation."""
        if not self._is_triad:
            logger.warning("ACCESS DENIED: Agent %s is not Shinobi no San", self._agent_id)
            return False

        if self._vault and self._vault.is_locked():
            logger.warning("ACCESS DENIED: Vault is in lockout mode")
            return False

        return True

    # =========================================================================
    # BROWSER OPERATIONS
    # =========================================================================

    async def launch_browser(self, session_name: str = "shinobi", headless: bool = True,
                             proxy: Optional[Dict[str, str]] = None) -> TaskResult:
        """Launch a browser session for web automation.

        Args:
            session_name: Name for the browser session (persistent cookies)
            headless: Run without visible window (True for servers)
            proxy: Optional proxy config {"server": "http://ip:port", "username": "...", "password": "..."}
                   Set RESIDENTIAL_PROXY env var for default proxy
        """
        if not self._check_access():
            return TaskResult(False, "Access denied", error="Not Triad member")

        # Check for residential proxy config
        if not proxy:
            residential_proxy = os.getenv("RESIDENTIAL_PROXY", "")
            if residential_proxy:
                # Format: "http://user:pass@ip:port" or just "http://ip:port"
                proxy = {"server": residential_proxy}
                logger.info("Using residential proxy from env: %s", residential_proxy.split('@')[-1])

        try:
            self._browser = BrowserAutomation(self._data_dir, headless=headless, proxy=proxy)
            success = await self._browser.launch(session_name)

            if success:
                # Inject CAPTCHA solver into browser for autonomous solving
                if self._captcha_integrator:
                    from .browser import set_captcha_solver
                    set_captcha_solver(self._captcha_integrator)
                    logger.info("AI CAPTCHA solver injected into browser")

                # Inject phone verification service for SMS verification
                if self._phone_service:
                    set_phone_service(self._phone_service)
                    await self._phone_service.initialize()
                    logger.info("Phone verification service injected into browser")

                logger.info("Browser launched by agent %s", self._agent_id)
                return TaskResult(True, f"Browser session '{session_name}' active")
            else:
                return TaskResult(False, "Browser launch failed", error="Playwright may not be installed")

        except Exception as e:
            return TaskResult(False, "Browser launch failed", error=str(e))

    async def navigate(self, url: str) -> TaskResult:
        """Navigate browser to URL."""
        if not self._check_access() or not self._browser:
            return TaskResult(False, "No active browser session")

        success = await self._browser.navigate(url)
        return TaskResult(success, f"Navigated to {url}" if success else "Navigation failed")

    async def create_email_account(self,
                                   provider: str,
                                   first_name: str,
                                   last_name: str,
                                   desired_username: str,
                                   password: str) -> TaskResult:
        """Create a new email account."""
        if not self._check_access():
            return TaskResult(False, "Access denied")

        # Ensure browser is running (headless for server environments)
        if not self._browser:
            result = await self.launch_browser(headless=True)
            if not result.success:
                return result

        creator = EmailCreator(self._browser)

        if provider.lower() == "gmail":
            result = await creator.create_gmail(
                first_name, last_name, desired_username, password
            )
        elif provider.lower() in ["protonmail", "proton"]:
            result = await creator.create_protonmail(desired_username, password)
        else:
            return TaskResult(False, f"Unknown provider: {provider}")

        if result.get("success"):
            # Store credentials in vault
            self._vault.store(
                name=f"email_{provider}_{desired_username}",
                credential_type="email",
                username=desired_username,
                password=password,
                email=result.get("email"),
                notes=f"Created by Shinobi agent {self._agent_id}"
            )
            return TaskResult(True, f"Email created: {result.get('email')}", data=result)
        else:
            return TaskResult(False, "Email creation failed", error=result.get("error"))

    async def register_platform(self,
                               platform: str,
                               email: str,
                               password: str,
                               **profile_data) -> TaskResult:
        """Register on a freelance platform."""
        if not self._check_access():
            return TaskResult(False, "Access denied")

        if not self._browser:
            result = await self.launch_browser(headless=True)
            if not result.success:
                return result

        registrar = PlatformRegistrar(self._browser)

        if platform.lower() == "upwork":
            result = await registrar.register_upwork(
                email=email,
                password=password,
                first_name=profile_data.get("first_name", "Jay"),
                last_name=profile_data.get("last_name", "Nelson")
            )
        elif platform.lower() == "fiverr":
            result = await registrar.register_fiverr(
                email=email,
                password=password,
                username=profile_data.get("username", "jaynelson_ai")
            )
        else:
            return TaskResult(False, f"Platform not yet supported: {platform}")

        if result.get("success"):
            # Store credentials
            self._vault.store(
                name=f"platform_{platform}",
                credential_type="platform",
                username=profile_data.get("username", email),
                password=password,
                email=email,
                url=f"https://{platform.lower()}.com",
                notes=f"Created by Shinobi agent {self._agent_id}"
            )
            return TaskResult(True, f"Registered on {platform}", data=result)
        else:
            return TaskResult(False, f"{platform} registration failed", error=result.get("error"))

    # =========================================================================
    # EMAIL OPERATIONS
    # =========================================================================

    async def setup_email(self, credential_name: str) -> TaskResult:
        """Initialize email client with stored credentials."""
        if not self._check_access():
            return TaskResult(False, "Access denied")

        cred = self._vault.get(credential_name, accessor=self._agent_id)
        if not cred:
            return TaskResult(False, f"Credential not found: {credential_name}")

        # Determine provider from email
        email = cred.email or cred.username
        if "gmail" in email:
            config = EmailConfig(**{**EMAIL_PROVIDERS["gmail"].__dict__,
                                   "email_address": email,
                                   "password": cred.password})
        elif "proton" in email:
            config = EmailConfig(**{**EMAIL_PROVIDERS["protonmail"].__dict__,
                                   "email_address": email,
                                   "password": cred.password})
        else:
            return TaskResult(False, f"Unknown email provider for: {email}")

        self._email_client = ShinobiEmailClient(config, self._data_dir)
        success = await self._email_client.connect()

        return TaskResult(success, "Email connected" if success else "Email connection failed")

    async def check_inbox(self, limit: int = 10, unread_only: bool = True) -> TaskResult:
        """Check email inbox."""
        if not self._check_access() or not self._email_client:
            return TaskResult(False, "Email not configured")

        messages = await self._email_client.get_inbox(limit, unread_only)

        return TaskResult(
            True,
            f"Found {len(messages)} messages",
            data={"messages": [
                {
                    "from": m.from_addr,
                    "subject": m.subject,
                    "date": m.date,
                    "preview": m.body[:200] if m.body else ""
                }
                for m in messages
            ]}
        )

    async def send_email(self, to: str, subject: str, body: str) -> TaskResult:
        """Send an email."""
        if not self._check_access() or not self._email_client:
            return TaskResult(False, "Email not configured")

        success = await self._email_client.send(to, subject, body)
        return TaskResult(success, f"Email sent to {to}" if success else "Send failed")

    async def reply_to_inquiry(self,
                               client_email: str,
                               client_name: str,
                               project_summary: str,
                               questions: List[str] = None) -> TaskResult:
        """Send a professional response to a project inquiry."""
        if not self._check_access() or not self._email_client:
            return TaskResult(False, "Email not configured")

        body = EmailTemplates.proposal_response(
            client_name=client_name,
            project_summary=project_summary,
            questions=questions or []
        )

        success = await self._email_client.send(
            to=client_email,
            subject=f"Re: Your Project Inquiry - Jay Nelson",
            body=body
        )

        return TaskResult(success, "Professional response sent" if success else "Send failed")

    # =========================================================================
    # HTTP / API OPERATIONS
    # =========================================================================

    async def fetch_url(self, url: str) -> TaskResult:
        """Fetch content from a URL."""
        if not self._check_access():
            return TaskResult(False, "Access denied")

        response = await self._http.get(url)

        if response.success:
            return TaskResult(True, f"Fetched {url}", data={
                "status": response.status_code,
                "body": response.body[:5000]
            })
        else:
            return TaskResult(False, "Fetch failed", error=response.error)

    async def call_api(self,
                       method: str,
                       url: str,
                       headers: Dict[str, str] = None,
                       data: Dict[str, Any] = None) -> TaskResult:
        """Make an API call."""
        if not self._check_access():
            return TaskResult(False, "Access denied")

        if method.upper() == "GET":
            response = await self._http.get(url, headers=headers, params=data)
        elif method.upper() == "POST":
            response = await self._http.post(url, headers=headers, json_body=data)
        elif method.upper() == "PUT":
            response = await self._http.put(url, headers=headers, json_body=data)
        elif method.upper() == "DELETE":
            response = await self._http.delete(url, headers=headers)
        else:
            return TaskResult(False, f"Unknown method: {method}")

        return TaskResult(
            response.success,
            f"API {method} {url}",
            data=response.json_data or {"body": response.body[:2000]}
        )

    # =========================================================================
    # AI-ASSISTED OPERATIONS
    # =========================================================================

    async def analyze_task(self, task_description: str) -> TaskResult:
        """Use Venice AI to analyze and plan a task."""
        if not self._check_access():
            return TaskResult(False, "Access denied")

        if not self._venice:
            return TaskResult(False, "Venice AI not configured (missing VENICE_API_KEY)")

        analysis = await self._venice.analyze_task(task_description)

        if "error" not in analysis:
            return TaskResult(True, "Task analyzed", data=analysis)
        else:
            return TaskResult(False, "Analysis failed", error=analysis.get("error"))

    # =========================================================================
    # AUTONOMOUS CAPTCHA SOLVING - 100% AI-native, NO human services
    # =========================================================================

    async def solve_captcha(self) -> TaskResult:
        """Detect and solve CAPTCHA on current browser page.

        Uses Venice AI vision model - completely autonomous.
        """
        if not self._check_access():
            return TaskResult(False, "Access denied")

        if not self._captcha_integrator:
            return TaskResult(False, "CAPTCHA solver not configured (missing VENICE_API_KEY)")

        if not self._browser:
            return TaskResult(False, "No active browser session")

        solution = await self._captcha_integrator.detect_and_solve(self._browser)

        if solution.success:
            logger.info("CAPTCHA solved: type=%s, confidence=%.2f, time=%.0fms",
                       solution.captcha_type, solution.confidence, solution.time_taken_ms)
            return TaskResult(
                True,
                f"CAPTCHA solved ({solution.captcha_type})",
                data={
                    "solution": solution.solution,
                    "captcha_type": solution.captcha_type,
                    "confidence": solution.confidence,
                    "time_ms": solution.time_taken_ms
                }
            )
        else:
            logger.warning("CAPTCHA solving failed: %s", solution.error)
            return TaskResult(
                False,
                "CAPTCHA solving failed",
                error=solution.error
            )

    async def solve_captcha_from_image(self, image_path: str) -> TaskResult:
        """Solve CAPTCHA from a specific image file.

        Args:
            image_path: Path to CAPTCHA image file

        Returns:
            TaskResult with solution
        """
        if not self._check_access():
            return TaskResult(False, "Access denied")

        if not self._captcha_solver:
            return TaskResult(False, "CAPTCHA solver not configured")

        from pathlib import Path
        path = Path(image_path)

        solution = await self._captcha_solver.solve_from_screenshot(path)

        return TaskResult(
            solution.success,
            f"Solution: {solution.solution}" if solution.success else "Failed",
            data={
                "solution": solution.solution,
                "captcha_type": solution.captcha_type,
                "confidence": solution.confidence
            },
            error=solution.error
        )

    async def solve_audio_captcha(self, audio_path: str) -> TaskResult:
        """Solve audio CAPTCHA using speech-to-text.

        Args:
            audio_path: Path to audio CAPTCHA file

        Returns:
            TaskResult with transcribed solution
        """
        if not self._check_access():
            return TaskResult(False, "Access denied")

        if not self._audio_solver:
            return TaskResult(False, "Audio solver not configured")

        from pathlib import Path
        path = Path(audio_path)

        solution = await self._audio_solver.solve_from_audio(path)

        return TaskResult(
            solution.success,
            f"Transcribed: {solution.solution}" if solution.success else "Failed",
            data={"solution": solution.solution},
            error=solution.error
        )

    def get_captcha_stats(self) -> TaskResult:
        """Get CAPTCHA solving statistics."""
        if not self._check_access():
            return TaskResult(False, "Access denied")

        if not self._captcha_solver:
            return TaskResult(False, "CAPTCHA solver not configured")

        return TaskResult(
            True,
            "CAPTCHA stats retrieved",
            data={
                "attempts": self._captcha_solver._attempts,
                "successes": self._captcha_solver._successes,
                "success_rate": self._captcha_solver.get_success_rate()
            }
        )

    async def draft_response(self, context: str, prompt: str) -> TaskResult:
        """Use AI to draft a professional response."""
        if not self._check_access():
            return TaskResult(False, "Access denied")

        if not self._venice:
            return TaskResult(False, "Venice AI not configured")

        full_prompt = f"""Context: {context}

Task: {prompt}

Write a professional, concise response that represents Jay Nelson, an elite web scraping and AI automation specialist."""

        response = await self._venice.complete(full_prompt)

        if response:
            return TaskResult(True, "Response drafted", data={"draft": response})
        else:
            return TaskResult(False, "Draft generation failed")

    # =========================================================================
    # CREDENTIAL MANAGEMENT
    # =========================================================================

    def list_credentials(self) -> TaskResult:
        """List stored credentials (no secrets exposed)."""
        if not self._check_access():
            return TaskResult(False, "Access denied")

        creds = self._vault.list_credentials()
        return TaskResult(True, f"Found {len(creds)} credentials", data={"credentials": creds})

    def get_credential(self, name: str) -> Optional[Credential]:
        """Get a specific credential."""
        if not self._check_access():
            return None

        return self._vault.get(name, accessor=self._agent_id)

    # =========================================================================
    # LEGACY INTERFACE (for backward compatibility)
    # =========================================================================

    def search_market(self, query: str) -> str:
        """Legacy market research interface."""
        if not self._is_triad:
            logger.warning("Access Denied: Agent %s attempted unauthorized internet access.", self._agent_id)
            return "ACCESS DENIED: Required Gift of Prophecy not found."

        # In the future, this would use real search APIs
        logger.info("Agent %s (Shinobi no San) accessing market data for: %s", self._agent_id, query)
        return f"DIVINE INSIGHT for '{query}': Market analysis requires full task execution. Use analyze_task() for detailed breakdown."

    def perform_fusion_task(self, task_description: str) -> str:
        """Legacy task execution interface."""
        if not self._is_triad:
            logger.warning("Access Denied: Agent %s attempted identity fusion without permission.", self._agent_id)
            return "FUSION DENIED: Authentication failure."

        logger.info("Identity Fusion Active: Shinobi no San member %s received task: %s", self._agent_id, task_description)
        return f"TASK QUEUED: '{task_description}' - Use async methods for full execution capabilities."

    # =========================================================================
    # CLEANUP
    # =========================================================================

    async def cleanup(self) -> None:
        """Close all connections."""
        if self._browser:
            await self._browser.close()
        if self._email_client:
            await self._email_client.disconnect()
        if self._http:
            await self._http.close()
