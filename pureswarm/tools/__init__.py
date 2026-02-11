"""Shinobi's Toolkit - External world capabilities for the Triad.

This package provides all the tools Shinobi no San needs to operate
in the outside world on behalf of the Sovereign.

SOVEREIGN OVERRIDE:
- All tools log to audit trail
- Vault has emergency lockout: from pureswarm.tools.vault import quick_lockout
- All credentials readable at: data/vault/SOVEREIGN_ACCESS.json

HUMANIZATION:
- All browser actions look like Jay's typing/mouse patterns
- Includes typos, corrections, variable speed, natural pauses
- Anti-detection built into every interaction
"""

from .internet import InternetAccess, TaskResult
from .vault import SovereignVault, Credential, quick_lockout, quick_export, quick_unlock
from .browser import BrowserAutomation, EmailCreator, PlatformRegistrar
from .http_client import ShinobiHTTPClient, VeniceAIClient
from .email_client import ShinobiEmailClient, EmailConfig, EmailTemplates
from .humanize import HumanBehavior, create_jay_profile, TypingProfile, MouseProfile, BehaviorProfile
from .captcha_solver import VisionCaptchaSolver, AudioCaptchaSolver, BrowserCaptchaIntegration, create_captcha_solver
from .phone_verify import PhoneVerificationService, RealSIMProvider, TwilioProvider, create_phone_service

__all__ = [
    # Main interface
    "InternetAccess",
    "TaskResult",

    # Vault (Sovereign access)
    "SovereignVault",
    "Credential",
    "quick_lockout",
    "quick_export",
    "quick_unlock",

    # Humanization (anti-detection)
    "HumanBehavior",
    "create_jay_profile",
    "TypingProfile",
    "MouseProfile",
    "BehaviorProfile",

    # AI CAPTCHA Solving (100% autonomous, NO human services)
    "VisionCaptchaSolver",
    "AudioCaptchaSolver",
    "BrowserCaptchaIntegration",
    "create_captcha_solver",

    # Phone Verification (Real SIM preferred, Twilio fallback)
    "PhoneVerificationService",
    "RealSIMProvider",
    "TwilioProvider",
    "create_phone_service",

    # Low-level tools (for advanced use)
    "BrowserAutomation",
    "EmailCreator",
    "PlatformRegistrar",
    "ShinobiHTTPClient",
    "VeniceAIClient",
    "ShinobiEmailClient",
    "EmailConfig",
    "EmailTemplates",
]
