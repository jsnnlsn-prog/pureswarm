"""Autonomous CAPTCHA Solver using AI Vision.

NO human services. 100% AI-native.
Uses Venice AI vision model to analyze and solve CAPTCHAs.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("pureswarm.tools.captcha_solver")


@dataclass
class CaptchaSolution:
    """Result of CAPTCHA solving attempt."""
    success: bool
    solution: str
    captcha_type: str
    confidence: float
    time_taken_ms: float
    error: Optional[str] = None


class VisionCaptchaSolver:
    """AI Vision-powered CAPTCHA solver.

    Uses Venice AI's vision model to:
    - Identify CAPTCHA types (image, text, audio)
    - Extract text from image CAPTCHAs
    - Solve image selection puzzles ("select all traffic lights")
    - Convert audio CAPTCHAs to text
    """

    # Venice AI vision model - confirmed from API
    VISION_MODEL = "qwen3-vl-235b-a22b"

    def __init__(self, api_key: str, http_client, data_dir: Path = None) -> None:
        self._api_key = api_key
        self._http = http_client
        self._data_dir = data_dir or Path("data")
        self._captcha_dir = self._data_dir / "captcha_solutions"
        self._captcha_dir.mkdir(parents=True, exist_ok=True)
        self._base_url = "https://api.venice.ai/api/v1"

        # Track success rate for learning
        self._attempts = 0
        self._successes = 0

    async def solve_from_screenshot(self, screenshot_path: Path) -> CaptchaSolution:
        """Solve CAPTCHA from a screenshot file."""
        start_time = asyncio.get_event_loop().time()

        if not screenshot_path.exists():
            return CaptchaSolution(
                success=False,
                solution="",
                captcha_type="unknown",
                confidence=0.0,
                time_taken_ms=0.0,
                error=f"Screenshot not found: {screenshot_path}"
            )

        # Read and encode image
        with open(screenshot_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # Determine image type from extension
        ext = screenshot_path.suffix.lower()
        media_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }.get(ext, "image/png")

        return await self._solve_with_vision(image_data, media_type, start_time)

    async def solve_from_bytes(self, image_bytes: bytes, media_type: str = "image/png") -> CaptchaSolution:
        """Solve CAPTCHA from raw image bytes."""
        start_time = asyncio.get_event_loop().time()
        image_data = base64.b64encode(image_bytes).decode("utf-8")
        return await self._solve_with_vision(image_data, media_type, start_time)

    async def solve_from_base64(self, image_b64: str, media_type: str = "image/png") -> CaptchaSolution:
        """Solve CAPTCHA from base64-encoded image."""
        start_time = asyncio.get_event_loop().time()
        return await self._solve_with_vision(image_b64, media_type, start_time)

    async def _solve_with_vision(self, image_b64: str, media_type: str, start_time: float) -> CaptchaSolution:
        """Core vision-based CAPTCHA solving."""
        self._attempts += 1

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        # Craft the CAPTCHA-solving prompt
        prompt = """You are a CAPTCHA solving assistant. Analyze this image and solve the CAPTCHA.

IMPORTANT: Respond ONLY with a JSON object in this exact format:
{
    "captcha_type": "text|image_selection|slider|audio|recaptcha|hcaptcha|cloudflare",
    "solution": "THE ANSWER HERE",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation"
}

For text CAPTCHAs: The solution is the text/characters shown.
For image selection ("select all X"): List the grid positions (1-9 for 3x3, 1-16 for 4x4) that contain the target.
For math CAPTCHAs: The solution is the numerical answer.
For slider CAPTCHAs: Describe the offset needed.

Be precise. The solution will be used programmatically."""

        payload = {
            "model": self.VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.1  # Low temp for accuracy
        }

        try:
            response = await self._http.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json_body=payload
            )

            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000

            if response.success and response.json_data:
                content = response.json_data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Parse JSON from response
                solution = self._parse_solution(content)

                if solution:
                    self._successes += 1
                    self._log_solution(solution, elapsed)
                    return CaptchaSolution(
                        success=True,
                        solution=solution.get("solution", ""),
                        captcha_type=solution.get("captcha_type", "unknown"),
                        confidence=float(solution.get("confidence", 0.5)),
                        time_taken_ms=elapsed
                    )

            return CaptchaSolution(
                success=False,
                solution="",
                captcha_type="unknown",
                confidence=0.0,
                time_taken_ms=elapsed,
                error=response.error or "Failed to parse vision response"
            )

        except Exception as e:
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error("Vision CAPTCHA solving failed: %s", e)
            return CaptchaSolution(
                success=False,
                solution="",
                captcha_type="unknown",
                confidence=0.0,
                time_taken_ms=elapsed,
                error=str(e)
            )

    def _parse_solution(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract JSON solution from model response."""
        try:
            # Try direct JSON parse
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object
        json_match = re.search(r'\{[^{}]*"solution"[^{}]*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse CAPTCHA solution from: %s", content[:200])
        return None

    def _log_solution(self, solution: Dict[str, Any], elapsed_ms: float) -> None:
        """Log CAPTCHA solution for analysis."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "captcha_type": solution.get("captcha_type"),
            "confidence": solution.get("confidence"),
            "time_ms": elapsed_ms,
            "success_rate": self._successes / self._attempts if self._attempts > 0 else 0
        }

        log_file = self._captcha_dir / "solutions.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    def get_success_rate(self) -> float:
        """Return current success rate."""
        return self._successes / self._attempts if self._attempts > 0 else 0.0


class AudioCaptchaSolver:
    """Solve audio CAPTCHAs using speech-to-text."""

    def __init__(self, api_key: str, http_client) -> None:
        self._api_key = api_key
        self._http = http_client
        self._base_url = "https://api.venice.ai/api/v1"

    async def solve_from_audio(self, audio_path: Path) -> CaptchaSolution:
        """Solve audio CAPTCHA by transcribing."""
        start_time = asyncio.get_event_loop().time()

        if not audio_path.exists():
            return CaptchaSolution(
                success=False,
                solution="",
                captcha_type="audio",
                confidence=0.0,
                time_taken_ms=0.0,
                error=f"Audio file not found: {audio_path}"
            )

        # Read audio file
        with open(audio_path, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        # Use Venice's audio transcription endpoint
        # Note: This may need adjustment based on actual Venice API
        payload = {
            "model": "whisper-large-v3",
            "audio": audio_data,
            "response_format": "text"
        }

        try:
            response = await self._http.post(
                f"{self._base_url}/audio/transcriptions",
                headers=headers,
                json_body=payload
            )

            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000

            if response.success:
                # Extract just the letters/numbers (CAPTCHAs usually say characters)
                text = response.body.strip()
                # Clean up common audio CAPTCHA patterns
                solution = self._extract_captcha_text(text)

                return CaptchaSolution(
                    success=bool(solution),
                    solution=solution,
                    captcha_type="audio",
                    confidence=0.8 if solution else 0.0,
                    time_taken_ms=elapsed
                )

            return CaptchaSolution(
                success=False,
                solution="",
                captcha_type="audio",
                confidence=0.0,
                time_taken_ms=elapsed,
                error=response.error
            )

        except Exception as e:
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            return CaptchaSolution(
                success=False,
                solution="",
                captcha_type="audio",
                confidence=0.0,
                time_taken_ms=elapsed,
                error=str(e)
            )

    def _extract_captcha_text(self, transcription: str) -> str:
        """Extract CAPTCHA characters from transcription.

        Audio CAPTCHAs typically say things like:
        "The characters are: A, B, 3, D, 7"
        "Type: delta, seven, bravo, three"
        """
        # Remove common filler
        text = transcription.lower()

        # NATO phonetic alphabet mapping
        phonetic = {
            "alpha": "a", "bravo": "b", "charlie": "c", "delta": "d",
            "echo": "e", "foxtrot": "f", "golf": "g", "hotel": "h",
            "india": "i", "juliet": "j", "kilo": "k", "lima": "l",
            "mike": "m", "november": "n", "oscar": "o", "papa": "p",
            "quebec": "q", "romeo": "r", "sierra": "s", "tango": "t",
            "uniform": "u", "victor": "v", "whiskey": "w", "xray": "x",
            "yankee": "y", "zulu": "z",
            "zero": "0", "one": "1", "two": "2", "three": "3",
            "four": "4", "five": "5", "six": "6", "seven": "7",
            "eight": "8", "nine": "9"
        }

        # Replace phonetic words
        for word, char in phonetic.items():
            text = text.replace(word, char)

        # Extract alphanumeric characters
        chars = re.findall(r'[a-z0-9]', text)

        # Return last sequence of reasonable length (3-8 chars typical)
        result = ''.join(chars)
        if 3 <= len(result) <= 8:
            return result.upper()

        # Try to find a reasonable substring
        for i in range(len(chars) - 3):
            substr = ''.join(chars[i:i+6])
            if len(substr) >= 3:
                return substr.upper()

        return result.upper() if result else ""


class BrowserCaptchaIntegration:
    """Integrates CAPTCHA solver with browser automation."""

    def __init__(self, vision_solver: VisionCaptchaSolver,
                 audio_solver: Optional[AudioCaptchaSolver] = None) -> None:
        self._vision = vision_solver
        self._audio = audio_solver

    async def detect_and_solve(self, browser) -> CaptchaSolution:
        """Detect CAPTCHA on current page and attempt to solve.

        Args:
            browser: BrowserAutomation instance with active page

        Returns:
            CaptchaSolution with result
        """
        if not browser._page:
            return CaptchaSolution(
                success=False,
                solution="",
                captcha_type="unknown",
                confidence=0.0,
                time_taken_ms=0.0,
                error="No active browser page"
            )

        page = browser._page

        # Check for common CAPTCHA indicators
        captcha_type = await self._detect_captcha_type(page)

        if captcha_type == "none":
            return CaptchaSolution(
                success=True,
                solution="",
                captcha_type="none",
                confidence=1.0,
                time_taken_ms=0.0
            )

        logger.info("Detected CAPTCHA type: %s", captcha_type)

        # Take screenshot of CAPTCHA area
        screenshot_path = await browser.screenshot(f"captcha_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        if not screenshot_path:
            return CaptchaSolution(
                success=False,
                solution="",
                captcha_type=captcha_type,
                confidence=0.0,
                time_taken_ms=0.0,
                error="Failed to capture CAPTCHA screenshot"
            )

        # Solve with vision
        solution = await self._vision.solve_from_screenshot(screenshot_path)

        if solution.success:
            # Attempt to input the solution
            await self._input_solution(page, solution, captcha_type)

        return solution

    async def _detect_captcha_type(self, page) -> str:
        """Detect what type of CAPTCHA is present."""
        try:
            # Check for reCAPTCHA
            recaptcha = await page.query_selector('iframe[src*="recaptcha"]')
            if recaptcha:
                return "recaptcha"

            # Check for hCaptcha
            hcaptcha = await page.query_selector('iframe[src*="hcaptcha"]')
            if hcaptcha:
                return "hcaptcha"

            # Check for Cloudflare challenge
            cloudflare = await page.query_selector('#challenge-form')
            if cloudflare:
                return "cloudflare"

            # Check for text input CAPTCHA
            captcha_input = await page.query_selector('input[name*="captcha"], input[id*="captcha"]')
            captcha_image = await page.query_selector('img[src*="captcha"], img[id*="captcha"]')
            if captcha_input and captcha_image:
                return "text"

            # Check for image selection
            challenge = await page.query_selector('.rc-imageselect, .challenge-images')
            if challenge:
                return "image_selection"

            return "none"

        except Exception as e:
            logger.error("CAPTCHA detection failed: %s", e)
            return "unknown"

    async def _input_solution(self, page, solution: CaptchaSolution, captcha_type: str) -> bool:
        """Input the CAPTCHA solution into the page."""
        try:
            if captcha_type == "text":
                # Find and fill text input
                input_sel = 'input[name*="captcha"], input[id*="captcha"]'
                await page.fill(input_sel, solution.solution)
                await asyncio.sleep(0.5)

                # Try to submit
                submit = await page.query_selector('button[type="submit"], input[type="submit"]')
                if submit:
                    await submit.click()

                return True

            elif captcha_type == "image_selection":
                # Parse grid positions from solution (e.g., "1,3,5,7")
                positions = [int(p.strip()) for p in solution.solution.split(",") if p.strip().isdigit()]

                # Click each position in the grid
                for pos in positions:
                    # Assuming 3x3 grid with tiles
                    tile_sel = f'.rc-imageselect-tile:nth-child({pos})'
                    tile = await page.query_selector(tile_sel)
                    if tile:
                        await tile.click()
                        await asyncio.sleep(0.3)

                # Click verify button
                verify = await page.query_selector('.rc-button-default')
                if verify:
                    await verify.click()

                return True

            elif captcha_type == "cloudflare":
                # Cloudflare usually just needs time and proper behavior
                # Wait for challenge to complete
                await asyncio.sleep(5)
                return True

            return False

        except Exception as e:
            logger.error("Failed to input CAPTCHA solution: %s", e)
            return False


# Factory function for easy instantiation
def create_captcha_solver(api_key: str, http_client, data_dir: Path = None):
    """Create a complete CAPTCHA solving system."""
    vision = VisionCaptchaSolver(api_key, http_client, data_dir)
    audio = AudioCaptchaSolver(api_key, http_client)
    integrator = BrowserCaptchaIntegration(vision, audio)

    return {
        "vision": vision,
        "audio": audio,
        "browser": integrator
    }
