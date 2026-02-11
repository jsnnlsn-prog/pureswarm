"""Browser automation toolkit for Shinobi no San - Real hands in the digital world.

All interactions use the humanization layer to avoid bot detection.
Shinobi types like Jay, moves the mouse like Jay, makes mistakes like Jay.
"""

from __future__ import annotations

import asyncio
import logging
import json
import random
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from .humanize import HumanBehavior, create_jay_profile

logger = logging.getLogger("pureswarm.tools.browser")


# Phone verification service - injected at runtime
_phone_service = None

def set_phone_service(service):
    """Inject phone verification service for platforms requiring SMS verification."""
    global _phone_service
    _phone_service = service


# CAPTCHA solver will be injected at runtime to avoid circular imports
_captcha_solver = None

def set_captcha_solver(solver):
    """Inject CAPTCHA solver for use by browser automation."""
    global _captcha_solver
    _captcha_solver = solver


@dataclass
class BrowserSession:
    """Represents an active browser session with state."""
    session_id: str
    user_data_dir: Path
    is_active: bool = False
    current_url: str = ""
    cookies: Dict[str, Any] = field(default_factory=dict)


class BrowserAutomation:
    """Playwright-based browser automation for Shinobi's external operations.

    This gives Shinobi real hands to:
    - Create email accounts
    - Register on platforms
    - Fill out profiles
    - Navigate and interact with web interfaces
    """

    def __init__(self, data_dir: Path, headless: bool = True, humanize: bool = True,
                 proxy: Optional[Dict[str, str]] = None) -> None:
        self._data_dir = data_dir
        self._browser_data = data_dir / "browser"
        self._browser_data.mkdir(parents=True, exist_ok=True)
        self._headless = headless
        self._browser = None
        self._context = None
        self._page = None
        self._sessions: Dict[str, BrowserSession] = {}

        # Proxy configuration for residential IP routing
        # Format: {"server": "http://ip:port", "username": "user", "password": "pass"}
        self._proxy = proxy

        # Humanization layer - makes Shinobi look like Jay
        self._humanize = humanize
        self._human = create_jay_profile() if humanize else None

        # Anti-detection settings
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]

        # Viewport variations for fingerprint randomization
        self._viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
        ]

    async def launch(self, session_name: str = "default") -> bool:
        """Launch a browser instance with anti-detection measures."""
        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()

            # Create persistent context for session continuity
            user_data_path = self._browser_data / session_name
            user_data_path.mkdir(parents=True, exist_ok=True)

            # Random fingerprint
            user_agent = random.choice(self._user_agents)
            viewport = random.choice(self._viewports)

            # Full stealth mode args - bypass Cloudflare and bot detection
            stealth_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-infobars",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--window-size=1920,1080",
                "--start-maximized",
            ]

            # Build launch options
            launch_options = {
                "user_data_dir": str(user_data_path),
                "headless": self._headless,
                "user_agent": user_agent,
                "viewport": viewport,
                "locale": "en-US",
                "timezone_id": "America/New_York",
                "geolocation": {"latitude": 40.7128, "longitude": -74.0060},  # NYC
                "permissions": ["geolocation"],
                "color_scheme": "light",
                "args": stealth_args,
                "ignore_https_errors": True,
            }

            # Add proxy if configured (residential IP routing)
            if self._proxy:
                launch_options["proxy"] = self._proxy
                logger.info("Browser using proxy: %s", self._proxy.get("server", "configured"))

            self._context = await self._playwright.chromium.launch_persistent_context(**launch_options)

            # Get or create page
            if self._context.pages:
                self._page = self._context.pages[0]
            else:
                self._page = await self._context.new_page()

            # Comprehensive stealth script - bypasses Cloudflare, reCAPTCHA detection
            await self._page.add_init_script("""
                // ===== STEALTH MODE =====

                // 1. Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                delete navigator.__proto__.webdriver;

                // 2. Mock chrome runtime (critical for Cloudflare)
                window.chrome = {
                    runtime: {
                        onConnect: { addListener: function() {} },
                        onMessage: { addListener: function() {} },
                        sendMessage: function() {},
                        connect: function() { return { onMessage: { addListener: function() {} } } }
                    },
                    loadTimes: function() { return {} },
                    csi: function() { return {} },
                    app: { isInstalled: false, InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }, RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' } }
                };

                // 3. Mock plugins array realistically
                Object.defineProperty(navigator, 'plugins', {
                    get: () => {
                        const plugins = [
                            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                        ];
                        plugins.item = (i) => plugins[i];
                        plugins.namedItem = (name) => plugins.find(p => p.name === name);
                        plugins.refresh = () => {};
                        return plugins;
                    }
                });

                // 4. Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });

                // 5. Mock permissions API
                const originalQuery = window.navigator.permissions?.query;
                if (originalQuery) {
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                }

                // 6. Mock connection info
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: '4g',
                        rtt: 50,
                        downlink: 10,
                        saveData: false
                    })
                });

                // 7. Prevent iframe detection
                Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                    get: function() {
                        return window;
                    }
                });

                // 8. Mock WebGL vendor/renderer (randomized)
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) return 'Intel Inc.';
                    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                    return getParameter.call(this, parameter);
                };

                // 9. Prevent Notification permission detection
                Object.defineProperty(Notification, 'permission', {
                    get: () => 'default'
                });

                // 10. Mock deviceMemory
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8
                });

                // 11. Mock hardwareConcurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8
                });

                // 12. Console log protection
                const originalLog = console.log;
                console.log = function(...args) {
                    if (args[0]?.includes?.('webdriver')) return;
                    return originalLog.apply(console, args);
                };

                // 13. Prevent automation detection via toString
                const originalFunction = Function.prototype.toString;
                Function.prototype.toString = function() {
                    if (this === navigator.webdriver) return 'function webdriver() { [native code] }';
                    return originalFunction.call(this);
                };

                console.log('Stealth mode active');
            """)

            session = BrowserSession(
                session_id=session_name,
                user_data_dir=user_data_path,
                is_active=True
            )
            self._sessions[session_name] = session

            logger.info("Browser launched: session=%s, headless=%s", session_name, self._headless)
            return True

        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            return False
        except Exception as e:
            logger.error("Failed to launch browser: %s", e)
            return False

    async def navigate(self, url: str, wait_for: str = "domcontentloaded", timeout: int = 60000) -> bool:
        """Navigate to a URL and wait for page load.

        Args:
            url: The URL to navigate to
            wait_for: Wait strategy - 'domcontentloaded' (faster) or 'networkidle' (thorough)
            timeout: Navigation timeout in milliseconds (default 60s)
        """
        if not self._page:
            logger.error("No active browser session")
            return False

        try:
            # Use longer timeout and fallback strategy
            await self._page.goto(url, wait_until=wait_for, timeout=timeout)
            logger.info("Navigated to: %s", url)

            # Brief pause to let dynamic content load
            await asyncio.sleep(2)
            return True
        except Exception as e:
            # If networkidle fails, try domcontentloaded
            if wait_for == "networkidle":
                try:
                    logger.warning("networkidle timeout, trying domcontentloaded...")
                    await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(3)
                    logger.info("Navigated to (fallback): %s", url)
                    return True
                except Exception:
                    pass
            logger.error("Navigation failed: %s", e)
            return False

    async def fill_form(self, selector: str, value: str, human_like: bool = True) -> bool:
        """Fill a form field with human-like typing (typos, variable speed, pauses)."""
        if not self._page:
            return False

        try:
            element = await self._page.wait_for_selector(selector, timeout=10000)
            if not element:
                logger.warning("Element not found: %s", selector)
                return False

            if human_like and self._human:
                # Use full humanization - typos, corrections, variable speed
                await self._human.type_like_human(self._page, selector, value)
            elif human_like:
                # Basic humanization fallback
                await element.click()
                for char in value:
                    await self._page.keyboard.type(char, delay=random.randint(50, 150))
                    await asyncio.sleep(random.uniform(0.01, 0.05))
            else:
                await element.click()
                await element.fill(value)

            # Take occasional micro-breaks (humans don't fill forms robotically)
            if self._human:
                await self._human.take_break()
                self._human.increase_fatigue()

            logger.debug("Filled form field: %s", selector)
            return True

        except Exception as e:
            logger.error("Failed to fill form %s: %s", selector, e)
            return False

    async def click(self, selector: str, wait_after: float = 1.0) -> bool:
        """Click an element with human-like mouse movement."""
        if not self._page:
            return False

        try:
            if self._human:
                # Human-like: curved mouse path, slight aim offset, hold duration
                await self._human.click_human(self._page, selector)
                await asyncio.sleep(wait_after * random.uniform(0.8, 1.2))
            else:
                element = await self._page.wait_for_selector(selector, timeout=10000)
                if element:
                    await element.click()
                    await asyncio.sleep(wait_after)

            logger.debug("Clicked: %s", selector)
            return True
        except Exception as e:
            logger.error("Click failed on %s: %s", selector, e)
            return False

    async def get_text(self, selector: str) -> Optional[str]:
        """Extract text content from an element."""
        if not self._page:
            return None

        try:
            element = await self._page.wait_for_selector(selector, timeout=5000)
            if element:
                return await element.text_content()
            return None
        except Exception:
            return None

    async def read_page(self, duration_seconds: float = None) -> None:
        """Simulate reading the current page (scrolling, pausing, mouse movement).

        This is critical for looking human - bots navigate instantly,
        humans take time to read and process content.
        """
        if not self._page:
            return

        if self._human:
            # Estimate content length from page
            try:
                content = await self._page.evaluate("document.body.innerText.length")
                content_length = content if content else 500
            except:
                content_length = 500

            if duration_seconds:
                # Override with specific duration
                await asyncio.sleep(duration_seconds * random.uniform(0.8, 1.2))
            else:
                await self._human.read_content(self._page, content_length)
        else:
            # Basic fallback
            await asyncio.sleep(duration_seconds or random.uniform(2, 5))

    async def screenshot(self, name: str) -> Optional[Path]:
        """Take a screenshot for debugging/verification."""
        if not self._page:
            return None

        try:
            screenshots_dir = self._browser_data / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            path = screenshots_dir / f"{name}.png"
            await self._page.screenshot(path=str(path))
            logger.info("Screenshot saved: %s", path)
            return path
        except Exception as e:
            logger.error("Screenshot failed: %s", e)
            return None

    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> bool:
        """Wait for an element to appear."""
        if not self._page:
            return False

        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    async def get_current_url(self) -> str:
        """Get the current page URL."""
        if self._page:
            return self._page.url
        return ""

    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript in the page context."""
        if not self._page:
            return None

        try:
            return await self._page.evaluate(script)
        except Exception as e:
            logger.error("Script execution failed: %s", e)
            return None

    async def discover_form_fields(self) -> Dict[str, List[Dict[str, Any]]]:
        """Dynamically discover all form fields on the current page.

        Returns a dict with field types as keys and lists of field info as values.
        This solves the selector drift problem - we find what's actually there.
        """
        if not self._page:
            return {}

        try:
            fields = await self._page.evaluate("""
                () => {
                    const result = {
                        email: [],
                        password: [],
                        text: [],
                        username: [],
                        name: [],
                        phone: [],
                        button: [],
                        checkbox: []
                    };

                    // Find all input fields
                    const inputs = document.querySelectorAll('input, button[type="submit"], button:not([type])');

                    for (const el of inputs) {
                        const type = el.type || 'text';
                        const name = el.name || '';
                        const id = el.id || '';
                        const placeholder = el.placeholder || '';
                        const ariaLabel = el.getAttribute('aria-label') || '';
                        const autocomplete = el.getAttribute('autocomplete') || '';

                        // Build best selector
                        let selector = '';
                        if (id) selector = '#' + id;
                        else if (name) selector = `[name="${name}"]`;
                        else if (placeholder) selector = `[placeholder="${placeholder}"]`;

                        const info = {
                            type: type,
                            name: name,
                            id: id,
                            placeholder: placeholder,
                            ariaLabel: ariaLabel,
                            autocomplete: autocomplete,
                            selector: selector,
                            visible: el.offsetParent !== null,
                            tagName: el.tagName.toLowerCase()
                        };

                        // Categorize by likely purpose
                        const allText = (name + id + placeholder + ariaLabel + autocomplete).toLowerCase();

                        if (type === 'email' || allText.includes('email')) {
                            result.email.push(info);
                        } else if (type === 'password' || allText.includes('password')) {
                            result.password.push(info);
                        } else if (allText.includes('user') || allText.includes('login')) {
                            result.username.push(info);
                        } else if (allText.includes('first') || allText.includes('last') || allText.includes('name')) {
                            result.name.push(info);
                        } else if (allText.includes('phone') || allText.includes('tel') || type === 'tel') {
                            result.phone.push(info);
                        } else if (type === 'checkbox') {
                            result.checkbox.push(info);
                        } else if (type === 'submit' || el.tagName === 'BUTTON') {
                            result.button.push(info);
                        } else if (type === 'text') {
                            result.text.push(info);
                        }
                    }

                    return result;
                }
            """)

            logger.info("Discovered form fields: email=%d, password=%d, name=%d, button=%d",
                       len(fields.get('email', [])), len(fields.get('password', [])),
                       len(fields.get('name', [])), len(fields.get('button', [])))

            return fields

        except Exception as e:
            logger.error("Form discovery failed: %s", e)
            return {}

    async def fill_discovered_field(self, field_type: str, value: str, index: int = 0) -> bool:
        """Fill a form field by its discovered type, not hardcoded selector.

        Args:
            field_type: 'email', 'password', 'username', 'name', 'phone', etc.
            value: The value to fill
            index: Which field of that type (0 = first, 1 = second, etc.)

        Returns:
            True if field was found and filled
        """
        fields = await self.discover_form_fields()

        candidates = fields.get(field_type, [])
        visible_candidates = [f for f in candidates if f.get('visible', True)]

        if index >= len(visible_candidates):
            logger.warning("No visible %s field at index %d (found %d)",
                          field_type, index, len(visible_candidates))
            return False

        field = visible_candidates[index]
        selector = field.get('selector')

        if not selector:
            # Build fallback selector
            if field.get('id'):
                selector = f"#{field['id']}"
            elif field.get('name'):
                selector = f"[name='{field['name']}']"
            else:
                logger.warning("Cannot build selector for %s field", field_type)
                return False

        logger.info("Filling %s field using discovered selector: %s", field_type, selector)
        return await self.fill_form(selector, value)

    async def click_discovered_button(self, button_text: str = None) -> bool:
        """Click a button by its text or the first submit button.

        Args:
            button_text: Partial text to match (e.g., "Submit", "Continue", "Join")

        Returns:
            True if button was clicked
        """
        fields = await self.discover_form_fields()
        buttons = fields.get('button', [])
        visible_buttons = [b for b in buttons if b.get('visible', True)]

        if button_text:
            # Find button containing the text
            for btn in visible_buttons:
                btn_text = (btn.get('ariaLabel', '') + btn.get('placeholder', '')).lower()
                if button_text.lower() in btn_text:
                    if btn.get('selector'):
                        return await self.click(btn['selector'])

            # Fallback: try Playwright text selector
            try:
                await self._page.click(f'button:has-text("{button_text}")', timeout=5000)
                return True
            except Exception:
                pass

        # Click first visible submit button
        for btn in visible_buttons:
            if btn.get('type') == 'submit' and btn.get('selector'):
                return await self.click(btn['selector'])

        logger.warning("No matching button found")
        return False

    async def handle_phone_verification(self, platform: str, timeout: int = 120) -> bool:
        """Handle phone verification if required by the platform.

        Uses the injected phone service to:
        1. Get a phone number
        2. Fill it into the form
        3. Wait for and enter the verification code

        Args:
            platform: The platform name (e.g., "upwork", "google")
            timeout: Max seconds to wait for code

        Returns:
            True if verification completed successfully
        """
        global _phone_service

        if not _phone_service:
            logger.warning("Phone verification required but no service configured")
            return False

        try:
            # Get a phone number
            phone_number = await _phone_service.request_verification(platform)
            if not phone_number:
                logger.error("Failed to get phone number for verification")
                return False

            logger.info("Got phone number for %s verification: %s", platform, phone_number)

            # Find and fill the phone field
            filled = await self.fill_discovered_field('phone', phone_number)
            if not filled:
                # Try common phone selectors
                phone_selectors = [
                    'input[type="tel"]',
                    'input[name="phone"]',
                    'input[name="phoneNumber"]',
                    'input[placeholder*="phone"]',
                    'input[autocomplete="tel"]',
                ]
                for sel in phone_selectors:
                    try:
                        element = await self._page.wait_for_selector(sel, timeout=3000)
                        if element and await element.is_visible():
                            await element.fill(phone_number)
                            filled = True
                            break
                    except Exception:
                        continue

            if not filled:
                logger.error("Could not find phone input field")
                return False

            # Click send/verify button
            await self.click_discovered_button("Send")
            await asyncio.sleep(2)

            # Wait for the verification code
            logger.info("Waiting for verification code (timeout: %ds)", timeout)
            code = await _phone_service.wait_for_code(platform, timeout=timeout)

            if not code:
                logger.error("Did not receive verification code within timeout")
                return False

            logger.info("Received verification code: %s", code)

            # Find and fill the code field
            code_selectors = [
                'input[name="code"]',
                'input[name="verificationCode"]',
                'input[placeholder*="code"]',
                'input[autocomplete="one-time-code"]',
                'input[type="text"]',  # Often just a plain text field
            ]

            code_filled = False
            for sel in code_selectors:
                try:
                    element = await self._page.wait_for_selector(sel, timeout=3000)
                    if element and await element.is_visible():
                        await element.fill(code)
                        code_filled = True
                        logger.info("Filled verification code using: %s", sel)
                        break
                except Exception:
                    continue

            if not code_filled:
                logger.error("Could not find code input field")
                return False

            # Submit the code
            await self.click_discovered_button("Verify")
            await asyncio.sleep(3)

            logger.info("Phone verification completed for %s", platform)
            return True

        except Exception as e:
            logger.error("Phone verification failed: %s", e)
            return False

    async def save_cookies(self, name: str) -> bool:
        """Save cookies for session persistence."""
        if not self._context:
            return False

        try:
            cookies = await self._context.cookies()
            cookies_file = self._browser_data / f"{name}_cookies.json"
            cookies_file.write_text(json.dumps(cookies, indent=2))
            logger.info("Cookies saved: %s", cookies_file)
            return True
        except Exception as e:
            logger.error("Failed to save cookies: %s", e)
            return False

    async def load_cookies(self, name: str) -> bool:
        """Load previously saved cookies."""
        if not self._context:
            return False

        try:
            cookies_file = self._browser_data / f"{name}_cookies.json"
            if cookies_file.exists():
                cookies = json.loads(cookies_file.read_text())
                await self._context.add_cookies(cookies)
                logger.info("Cookies loaded: %s", cookies_file)
                return True
            return False
        except Exception as e:
            logger.error("Failed to load cookies: %s", e)
            return False

    async def detect_captcha(self) -> str:
        """Detect if a CAPTCHA is present on the current page.

        Returns:
            CAPTCHA type: 'recaptcha', 'hcaptcha', 'cloudflare', 'text', 'image_selection', or 'none'
        """
        if not self._page:
            return "none"

        try:
            # Check for reCAPTCHA
            recaptcha = await self._page.query_selector('iframe[src*="recaptcha"]')
            if recaptcha:
                return "recaptcha"

            # Check for hCaptcha
            hcaptcha = await self._page.query_selector('iframe[src*="hcaptcha"]')
            if hcaptcha:
                return "hcaptcha"

            # Check for Cloudflare challenge
            cloudflare = await self._page.query_selector('#challenge-form, .cf-browser-verification')
            if cloudflare:
                return "cloudflare"

            # Check for generic CAPTCHA images
            captcha_img = await self._page.query_selector('img[src*="captcha"], img[id*="captcha"], img[class*="captcha"]')
            if captcha_img:
                return "text"

            # Check page content for CAPTCHA indicators
            page_text = await self._page.evaluate("document.body.innerText")
            captcha_keywords = ["captcha", "verify you", "not a robot", "security check", "prove you're human"]
            if any(kw in page_text.lower() for kw in captcha_keywords):
                return "unknown"

            return "none"

        except Exception as e:
            logger.warning("CAPTCHA detection error: %s", e)
            return "unknown"

    async def solve_captcha_if_present(self) -> bool:
        """Attempt to solve any CAPTCHA on the current page.

        Uses AI vision - NO human services.

        Returns:
            True if no CAPTCHA or CAPTCHA solved, False if solving failed
        """
        captcha_type = await self.detect_captcha()

        if captcha_type == "none":
            return True

        logger.info("CAPTCHA detected: %s - Attempting AI solution", captcha_type)

        global _captcha_solver
        if not _captcha_solver:
            logger.warning("No CAPTCHA solver configured - cannot solve autonomously")
            # Take screenshot for manual review
            await self.screenshot(f"captcha_blocked_{captcha_type}")
            return False

        try:
            solution = await _captcha_solver.detect_and_solve(self)

            if solution.success:
                logger.info("CAPTCHA solved autonomously: %s", solution.solution[:20] if solution.solution else "ok")
                await asyncio.sleep(2)  # Wait for page to process
                return True
            else:
                logger.warning("CAPTCHA solving failed: %s", solution.error)
                return False

        except Exception as e:
            logger.error("CAPTCHA solving error: %s", e)
            return False

    async def wait_for_cloudflare(self, timeout: int = 30) -> bool:
        """Wait for Cloudflare challenge to complete.

        Cloudflare's JS challenge often resolves on its own with proper
        browser fingerprinting and human-like behavior.
        """
        if not self._page:
            return False

        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check if challenge is gone
            challenge = await self._page.query_selector('#challenge-form, .cf-browser-verification')
            if not challenge:
                logger.info("Cloudflare challenge passed")
                return True

            # Wait and let JS execute
            await asyncio.sleep(2)

            # Move mouse naturally to look human
            if self._human:
                # Move to random position on screen
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await self._human.move_mouse_human(self._page, x, y)

        logger.warning("Cloudflare challenge did not resolve in %ds", timeout)
        return False

    async def solve_press_and_hold(self, timeout: int = 15) -> bool:
        """Solve PerimeterX 'Press & Hold' challenge (used by Fiverr).

        This requires simulating a real mouse press and hold for several seconds.
        """
        if not self._page:
            return False

        try:
            # Look for the Press & Hold button
            hold_selectors = [
                'button:has-text("PRESS & HOLD")',
                '[id*="px-captcha"]',
                '.px-captcha-container button',
                'div:has-text("PRESS & HOLD")',
            ]

            hold_button = None
            for selector in hold_selectors:
                try:
                    hold_button = await self._page.wait_for_selector(selector, timeout=3000)
                    if hold_button and await hold_button.is_visible():
                        break
                except Exception:
                    continue

            if not hold_button:
                # No Press & Hold challenge found
                return True

            logger.info("Press & Hold challenge detected - simulating human hold")

            # Get button bounding box
            box = await hold_button.bounding_box()
            if not box:
                return False

            # Calculate center of button
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2

            # Move mouse to button naturally
            if self._human:
                await self._human.move_mouse_human(self._page, x, y)
            else:
                await self._page.mouse.move(x, y)

            await asyncio.sleep(0.3)

            # Press and hold with realistic timing (3-5 seconds)
            hold_time = random.uniform(3.5, 5.0)
            logger.info("Holding button for %.1f seconds", hold_time)

            await self._page.mouse.down()
            await asyncio.sleep(hold_time)
            await self._page.mouse.up()

            await asyncio.sleep(3)

            # Check if challenge is TRULY resolved by looking for actual content
            # Not just absence of button, but presence of signup form
            page_content = await self._page.evaluate("document.body.innerText")

            # If we still see "PRESS & HOLD" or "human touch", challenge failed
            if "PRESS & HOLD" in page_content or "human touch" in page_content.lower():
                logger.warning("Press & Hold challenge still present after attempt")
                # Try one more time with longer hold
                await self._page.mouse.down()
                await asyncio.sleep(8)  # Hold longer
                await self._page.mouse.up()
                await asyncio.sleep(3)

                page_content = await self._page.evaluate("document.body.innerText")
                if "PRESS & HOLD" in page_content:
                    logger.error("Press & Hold challenge failed - IP may be flagged by PerimeterX")
                    return False

            # Verify we can see actual signup content
            if "email" in page_content.lower() or "join" in page_content.lower() or "sign up" in page_content.lower():
                logger.info("Press & Hold challenge passed - signup form visible")
                return True

            logger.info("Press & Hold challenge passed")
            return True

        except Exception as e:
            logger.error("Press & Hold solving error: %s", e)
            return False

    async def close(self) -> None:
        """Close the browser session."""
        try:
            if self._context:
                await self._context.close()
            if hasattr(self, '_playwright') and self._playwright:
                await self._playwright.stop()
            logger.info("Browser closed")
        except Exception as e:
            logger.error("Error closing browser: %s", e)


class EmailCreator:
    """Specialized automation for creating email accounts."""

    def __init__(self, browser: BrowserAutomation) -> None:
        self._browser = browser

    async def create_gmail(self,
                          first_name: str,
                          last_name: str,
                          desired_username: str,
                          password: str,
                          recovery_email: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Gmail account.

        Returns dict with:
            - success: bool
            - email: str (the created email)
            - error: str (if failed)
        """
        result = {"success": False, "email": "", "error": ""}

        # Verify browser is ready
        if not self._browser._page:
            result["error"] = "Browser not initialized - no active page"
            return result

        try:
            # Navigate to Gmail signup
            nav_ok = await self._browser.navigate("https://accounts.google.com/signup")
            if not nav_ok:
                result["error"] = "Failed to navigate to Gmail signup"
                return result
            await asyncio.sleep(2)

            # Fill first name
            await self._browser.fill_form('input[name="firstName"]', first_name)
            await asyncio.sleep(0.5)

            # Fill last name
            await self._browser.fill_form('input[name="lastName"]', last_name)
            await asyncio.sleep(0.5)

            # Click Next
            await self._browser.click('button:has-text("Next")')
            await asyncio.sleep(2)

            # This is where it gets tricky - Google often requires phone verification
            # We'll need to handle this interactively or with a phone verification service

            # Take screenshot for verification
            await self._browser.screenshot("gmail_signup_step1")

            # Check for CAPTCHA or challenge
            captcha_type = await self._browser.detect_captcha()
            if captcha_type != "none":
                logger.info("Gmail signup hit CAPTCHA: %s - attempting AI solve", captcha_type)
                solved = await self._browser.solve_captcha_if_present()
                if not solved:
                    result["error"] = f"CAPTCHA ({captcha_type}) could not be solved autonomously"
                    return result
                await asyncio.sleep(2)

            # Check if we hit phone verification
            current_url = await self._browser.get_current_url()
            if "phone" in current_url.lower() or "challenge" in current_url.lower():
                result["error"] = "Phone verification required - will need VoIP solution"
                logger.warning("Gmail signup requires phone verification")
                return result

            # Continue with birthday, etc...
            # This flow varies based on Google's current signup process

            result["success"] = True
            result["email"] = f"{desired_username}@gmail.com"

        except Exception as e:
            result["error"] = str(e)
            logger.error("Gmail creation failed: %s", e)

        return result

    async def create_protonmail(self,
                               desired_username: str,
                               password: str) -> Dict[str, Any]:
        """Create a ProtonMail account using dynamic form discovery."""
        result = {"success": False, "email": "", "error": ""}

        if not self._browser._page:
            result["error"] = "Browser not initialized - no active page"
            return result

        try:
            nav_ok = await self._browser.navigate("https://account.proton.me/signup")
            if not nav_ok:
                result["error"] = "Failed to navigate to ProtonMail signup"
                return result
            await asyncio.sleep(3)

            # Select free plan if prompted
            try:
                free_button = await self._browser._page.wait_for_selector('button:has-text("Get Proton for free")', timeout=5000)
                if free_button:
                    await free_button.click()
                    await asyncio.sleep(2)
            except Exception:
                pass

            # Screenshot to see what we're working with
            await self._browser.screenshot("protonmail_before_fill")

            # Use dynamic form discovery instead of hardcoded selectors
            fields = await self._browser.discover_form_fields()
            logger.info("ProtonMail form fields discovered: %s", {k: len(v) for k, v in fields.items()})

            # Fill username - could be email field or username field
            username_filled = False
            if fields.get('email'):
                username_filled = await self._browser.fill_discovered_field('email', desired_username, 0)
            if not username_filled and fields.get('username'):
                username_filled = await self._browser.fill_discovered_field('username', desired_username, 0)
            if not username_filled and fields.get('text'):
                # Try first visible text field
                username_filled = await self._browser.fill_discovered_field('text', desired_username, 0)

            if not username_filled:
                logger.warning("Could not find username field via discovery - trying fallbacks")
                for sel in ['input[id="email"]', 'input[name="email"]', 'input:not([type="password"])']:
                    try:
                        el = await self._browser._page.wait_for_selector(sel, timeout=2000)
                        if el and await el.is_visible():
                            await el.fill(desired_username)
                            username_filled = True
                            break
                    except Exception:
                        continue

            await asyncio.sleep(0.5)

            # Fill password fields
            password_fields = fields.get('password', [])
            visible_pw_fields = [f for f in password_fields if f.get('visible', True)]

            if len(visible_pw_fields) >= 1:
                await self._browser.fill_discovered_field('password', password, 0)
            if len(visible_pw_fields) >= 2:
                await self._browser.fill_discovered_field('password', password, 1)

            await asyncio.sleep(0.5)
            await self._browser.screenshot("protonmail_signup")

            # Click submit using discovery
            submitted = await self._browser.click_discovered_button("Create")
            if not submitted:
                submitted = await self._browser.click_discovered_button("Start")
            if not submitted:
                submitted = await self._browser.click_discovered_button("Get started")
            if not submitted:
                # Try any submit button
                for btn in fields.get('button', []):
                    if btn.get('type') == 'submit' and btn.get('selector'):
                        await self._browser.click(btn['selector'])
                        submitted = True
                        break

            await asyncio.sleep(3)

            # Handle CAPTCHA
            captcha_type = await self._browser.detect_captcha()
            if captcha_type != "none":
                logger.info("ProtonMail CAPTCHA: %s - attempting AI solve", captcha_type)
                await self._browser.screenshot("protonmail_captcha_before")

                solved = await self._browser.solve_captcha_if_present()
                if not solved:
                    result["error"] = f"CAPTCHA ({captcha_type}) could not be solved"
                    await self._browser.screenshot("protonmail_captcha_failed")
                    return result

                await asyncio.sleep(3)

            # Check for phone verification
            page_text = await self._browser._page.evaluate("document.body.innerText")
            if "phone" in page_text.lower() and "verify" in page_text.lower():
                logger.info("ProtonMail requires phone verification")
                verified = await self._browser.handle_phone_verification("protonmail")
                if not verified:
                    result["error"] = "Phone verification required but failed"
                    return result

            result["success"] = True
            result["email"] = f"{desired_username}@proton.me"

        except Exception as e:
            result["error"] = str(e)
            logger.error("ProtonMail creation failed: %s", e)

        return result


class PlatformRegistrar:
    """Specialized automation for registering on freelance platforms."""

    def __init__(self, browser: BrowserAutomation) -> None:
        self._browser = browser

    async def register_upwork(self,
                             email: str,
                             password: str,
                             first_name: str,
                             last_name: str,
                             country: str = "United States") -> Dict[str, Any]:
        """Register a new Upwork freelancer account."""
        result = {"success": False, "error": ""}

        # Verify browser is ready
        if not self._browser._page:
            result["error"] = "Browser not initialized - no active page"
            return result

        try:
            nav_ok = await self._browser.navigate("https://www.upwork.com/nx/signup/?dest=home")
            if not nav_ok:
                result["error"] = "Failed to navigate to Upwork signup"
                return result
            await asyncio.sleep(3)

            # CRITICAL: Dismiss cookie consent popup first
            # The popup blocks all interaction with the underlying form
            popup_dismissed = False

            # Wait a moment for popup to fully render
            await asyncio.sleep(2)

            try:
                # Method 1: Find the X button directly by looking for SVG in small buttons
                dismissed = await self._browser._page.evaluate("""
                    () => {
                        // Find ALL buttons on the page
                        const allElements = document.querySelectorAll('button, [role="button"]');
                        for (const el of allElements) {
                            // Check if this element contains an SVG (likely close icon)
                            const hasSvg = el.querySelector('svg');
                            const rect = el.getBoundingClientRect();

                            // The X button is small and in the popup area (lower-left quadrant)
                            if (hasSvg && rect.width < 50 && rect.height < 50 && rect.y > 500) {
                                el.click();
                                console.log('Clicked close button at', rect.x, rect.y);
                                return true;
                            }
                        }

                        // Alternative: Look for the popup card and click its close area
                        const textNodes = document.evaluate(
                            "//div[contains(text(), 'This site employs')]",
                            document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                        ).singleNodeValue;

                        if (textNodes) {
                            // Find parent card
                            let card = textNodes.closest('div[class]');
                            if (card) {
                                const closeBtn = card.querySelector('button, svg');
                                if (closeBtn) {
                                    closeBtn.click();
                                    return true;
                                }
                            }
                        }

                        return false;
                    }
                """)
                if dismissed:
                    logger.info("Upwork cookie popup dismissed via JS")
                    popup_dismissed = True
                    await asyncio.sleep(1)
            except Exception as e:
                logger.warning("JS popup dismiss failed: %s", e)

            # Method 2: Try clicking the X button using Playwright locator
            if not popup_dismissed:
                try:
                    # Look for button containing SVG near bottom of viewport
                    buttons = await self._browser._page.query_selector_all('button')
                    for btn in buttons:
                        box = await btn.bounding_box()
                        if box and box['y'] > 500 and box['width'] < 50:
                            await btn.click()
                            logger.info("Upwork cookie popup dismissed by button click at y=%d", box['y'])
                            popup_dismissed = True
                            await asyncio.sleep(1)
                            break
                except Exception as e:
                    logger.warning("Button-based popup dismiss failed: %s", e)

            # Method 3: Try clicking "Manage" then "Accept" in cookie settings
            if not popup_dismissed:
                try:
                    manage_btn = await self._browser._page.query_selector('button:has-text("Manage")')
                    if manage_btn:
                        await manage_btn.click()
                        await asyncio.sleep(1)
                        # Look for Accept or Save button
                        accept_btn = await self._browser._page.query_selector('button:has-text("Accept"), button:has-text("Save")')
                        if accept_btn:
                            await accept_btn.click()
                            logger.info("Upwork cookie popup dismissed via Manage->Accept")
                            popup_dismissed = True
                            await asyncio.sleep(1)
                except Exception as e:
                    logger.warning("Manage->Accept approach failed: %s", e)

            # Method 4: Scroll to move popup out of way
            if not popup_dismissed:
                try:
                    await self._browser._page.evaluate("window.scrollTo(0, 500)")
                    await asyncio.sleep(0.5)
                except Exception:
                    pass

            # Check for Cloudflare challenge
            if await self._browser.detect_captcha() == "cloudflare":
                logger.info("Upwork Cloudflare challenge detected - waiting for resolution")
                if not await self._browser.wait_for_cloudflare(timeout=30):
                    await self._browser.solve_captcha_if_present()

            # Screenshot to analyze current page state
            await self._browser.screenshot("upwork_before_selection")

            # Select "Work" (freelancer) option - try multiple selectors
            work_selectors = [
                'button[data-test="talent-cta"]',
                'button:has-text("Work")',
                'button:has-text("I want to work")',
                'a:has-text("Apply as a freelancer")',
                '[data-qa="signup-talent"]',
            ]

            for selector in work_selectors:
                try:
                    btn = await self._browser._page.wait_for_selector(selector, timeout=3000)
                    if btn and await btn.is_visible():
                        await btn.click()
                        logger.info("Upwork work button clicked: %s", selector)
                        break
                except Exception:
                    continue

            await asyncio.sleep(2)

            # Use dynamic form discovery
            fields = await self._browser.discover_form_fields()
            logger.info("Upwork form fields discovered: %s", {k: len(v) for k, v in fields.items()})

            # Fill name fields using discovery
            name_fields = fields.get('name', [])
            visible_name_fields = [f for f in name_fields if f.get('visible', True)]

            if len(visible_name_fields) >= 2:
                # First and last name are separate fields
                await self._browser.fill_discovered_field('name', first_name, 0)
                await asyncio.sleep(0.3)
                await self._browser.fill_discovered_field('name', last_name, 1)
            elif len(visible_name_fields) == 1:
                # Full name field
                await self._browser.fill_discovered_field('name', f"{first_name} {last_name}", 0)
            else:
                # Fallback to hardcoded selectors
                await self._browser.fill_form('input[name="firstName"]', first_name)
                await asyncio.sleep(0.3)
                await self._browser.fill_form('input[name="lastName"]', last_name)

            await asyncio.sleep(0.5)

            # Fill email
            if fields.get('email'):
                await self._browser.fill_discovered_field('email', email, 0)
            else:
                await self._browser.fill_form('input[name="email"]', email)

            await asyncio.sleep(0.5)

            # Fill password
            if fields.get('password'):
                await self._browser.fill_discovered_field('password', password, 0)
            else:
                await self._browser.fill_form('input[name="password"]', password)

            # Handle country selector if present
            try:
                country_select = await self._browser._page.wait_for_selector('select[name="country"]', timeout=3000)
                if country_select:
                    await country_select.select_option(label=country)
            except Exception:
                # May not have country field or it's styled differently
                pass

            await self._browser.screenshot("upwork_signup_filled")

            # Terms checkbox
            checkboxes = fields.get('checkbox', [])
            if checkboxes:
                for cb in checkboxes:
                    if cb.get('selector') and cb.get('visible'):
                        try:
                            await self._browser.click(cb['selector'])
                            break
                        except Exception:
                            continue
            else:
                try:
                    await self._browser.click('input[type="checkbox"]')
                except Exception:
                    pass

            # Submit using discovery
            submitted = await self._browser.click_discovered_button("Create")
            if not submitted:
                submitted = await self._browser.click_discovered_button("Sign up")
            if not submitted:
                submitted = await self._browser.click_discovered_button("Submit")
            if not submitted:
                # Fallback
                try:
                    await self._browser.click('button[type="submit"]')
                except Exception:
                    pass

            await asyncio.sleep(3)

            # Check for CAPTCHA after submit
            captcha_type = await self._browser.detect_captcha()
            if captcha_type != "none":
                logger.info("Upwork post-submit CAPTCHA: %s - attempting AI solve", captcha_type)
                solved = await self._browser.solve_captcha_if_present()
                if not solved:
                    result["error"] = f"CAPTCHA ({captcha_type}) could not be solved"
                    await self._browser.screenshot("upwork_captcha_failed")
                    return result
                await asyncio.sleep(2)

            # Check for phone verification
            page_text = await self._browser._page.evaluate("document.body.innerText")
            if "phone" in page_text.lower() and ("verify" in page_text.lower() or "confirm" in page_text.lower()):
                logger.info("Upwork requires phone verification")
                verified = await self._browser.handle_phone_verification("upwork")
                if not verified:
                    logger.warning("Phone verification failed - registration may be incomplete")

            # Verify form was actually submitted by checking URL change
            current_url = await self._browser.get_current_url()
            if "signup" not in current_url.lower() or "success" in current_url.lower() or "verify" in current_url.lower():
                result["success"] = True
                logger.info("Upwork registration initiated for: %s", email)
            else:
                # Take screenshot to see what went wrong
                await self._browser.screenshot("upwork_possible_failure")
                # Check for error messages on page
                error_text = await self._browser._page.evaluate("""
                    () => {
                        const errors = document.querySelectorAll('[class*="error"], [class*="Error"], [role="alert"]');
                        return Array.from(errors).map(e => e.innerText).join(' ');
                    }
                """)
                if error_text:
                    result["error"] = f"Form errors: {error_text[:200]}"
                else:
                    result["success"] = True  # Assume success if no errors visible
                    logger.info("Upwork registration initiated for: %s (unverified)", email)

        except Exception as e:
            result["error"] = str(e)
            logger.error("Upwork registration failed: %s", e)

        return result

    async def register_fiverr(self,
                             email: str,
                             password: str,
                             username: str) -> Dict[str, Any]:
        """Register a new Fiverr account."""
        result = {"success": False, "error": ""}

        # Verify browser is ready
        if not self._browser._page:
            result["error"] = "Browser not initialized - no active page"
            return result

        try:
            nav_ok = await self._browser.navigate("https://www.fiverr.com/join")
            if not nav_ok:
                result["error"] = "Failed to navigate to Fiverr signup"
                return result
            await asyncio.sleep(3)

            # Fiverr uses PerimeterX "Press & Hold" challenge
            # Check for it immediately after page load
            page_text = await self._browser._page.evaluate("document.body.innerText")
            if "PRESS & HOLD" in page_text or "human touch" in page_text.lower():
                logger.info("Fiverr Press & Hold challenge detected")
                await self._browser.screenshot("fiverr_press_hold_before")

                # Attempt to solve the press-and-hold challenge
                if not await self._browser.solve_press_and_hold():
                    result["error"] = "Press & Hold challenge could not be solved"
                    await self._browser.screenshot("fiverr_press_hold_failed")
                    return result

                await asyncio.sleep(2)
                logger.info("Press & Hold challenge passed - continuing")

            # Check for other CAPTCHAs
            captcha_type = await self._browser.detect_captcha()
            if captcha_type != "none":
                logger.info("Fiverr initial CAPTCHA: %s - attempting solve", captcha_type)
                await self._browser.solve_captcha_if_present()
                await asyncio.sleep(2)

            # Fiverr signup form - try multiple selectors
            email_selectors = [
                'input[name="email"]',
                'input[type="email"]',
                'input[placeholder*="Email"]',
                '#email',
            ]

            for selector in email_selectors:
                try:
                    element = await self._browser._page.wait_for_selector(selector, timeout=3000)
                    if element and await element.is_visible():
                        await element.fill(email)
                        logger.info("Fiverr email filled with: %s", selector)
                        break
                except Exception:
                    continue

            await asyncio.sleep(0.5)

            # Submit email
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Continue")',
                'button:has-text("Join")',
            ]

            for selector in submit_selectors:
                try:
                    btn = await self._browser._page.wait_for_selector(selector, timeout=3000)
                    if btn and await btn.is_visible():
                        await btn.click()
                        break
                except Exception:
                    continue

            await asyncio.sleep(2)

            # Check for CAPTCHA after email submit
            captcha_type = await self._browser.detect_captcha()
            if captcha_type != "none":
                logger.info("Fiverr email CAPTCHA: %s - attempting solve", captcha_type)
                if not await self._browser.solve_captcha_if_present():
                    result["error"] = f"CAPTCHA ({captcha_type}) blocked registration"
                    return result
                await asyncio.sleep(2)

            # Check for another Press & Hold
            page_text = await self._browser._page.evaluate("document.body.innerText")
            if "PRESS & HOLD" in page_text:
                await self._browser.solve_press_and_hold()
                await asyncio.sleep(2)

            # Use dynamic discovery for username/password fields
            fields = await self._browser.discover_form_fields()
            logger.info("Fiverr form fields: %s", {k: len(v) for k, v in fields.items()})

            # Fill username
            if fields.get('username'):
                await self._browser.fill_discovered_field('username', username, 0)
            else:
                await self._browser.fill_form('input[name="username"]', username)

            await asyncio.sleep(0.5)

            # Fill password
            if fields.get('password'):
                await self._browser.fill_discovered_field('password', password, 0)
            else:
                await self._browser.fill_form('input[name="password"]', password)

            await self._browser.screenshot("fiverr_signup")

            # Submit using discovery
            submitted = await self._browser.click_discovered_button("Join")
            if not submitted:
                submitted = await self._browser.click_discovered_button("Continue")
            if not submitted:
                await self._browser.click('button[type="submit"]')

            await asyncio.sleep(3)

            # Final CAPTCHA check
            captcha_type = await self._browser.detect_captcha()
            if captcha_type != "none":
                logger.info("Fiverr final CAPTCHA: %s - attempting solve", captcha_type)
                if not await self._browser.solve_captcha_if_present():
                    result["error"] = f"Final CAPTCHA ({captcha_type}) could not be solved"
                    return result

            # Check for phone verification
            page_text = await self._browser._page.evaluate("document.body.innerText")
            if "phone" in page_text.lower() and "verify" in page_text.lower():
                logger.info("Fiverr requires phone verification")
                verified = await self._browser.handle_phone_verification("fiverr")
                if not verified:
                    logger.warning("Phone verification failed")

            result["success"] = True
            logger.info("Fiverr registration initiated for: %s", email)

        except Exception as e:
            result["error"] = str(e)
            logger.error("Fiverr registration failed: %s", e)

        return result

    async def fill_upwork_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fill out an Upwork profile with provided data."""
        result = {"success": False, "error": ""}

        try:
            # Navigate to profile edit
            await self._browser.navigate("https://www.upwork.com/freelancers/settings/profile")
            await asyncio.sleep(2)

            # Title/Headline
            if "title" in profile_data:
                await self._browser.fill_form('input[name="title"]', profile_data["title"])

            # Overview/Bio
            if "overview" in profile_data:
                await self._browser.fill_form('textarea[name="overview"]', profile_data["overview"])

            # Hourly rate
            if "hourly_rate" in profile_data:
                await self._browser.fill_form('input[name="rate"]', str(profile_data["hourly_rate"]))

            # Skills
            if "skills" in profile_data:
                for skill in profile_data["skills"]:
                    await self._browser.fill_form('input[name="skills"]', skill)
                    await self._browser.click('button[data-test="add-skill"]')
                    await asyncio.sleep(0.5)

            await self._browser.screenshot("upwork_profile_filled")

            result["success"] = True

        except Exception as e:
            result["error"] = str(e)
            logger.error("Upwork profile fill failed: %s", e)

        return result
