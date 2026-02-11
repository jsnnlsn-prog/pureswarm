"""Humanization Layer - Make Shinobi look like Jay.

Bots get flagged because they're too perfect. This module adds
realistic human imperfections to all browser interactions.

Based on behavioral biometrics research - typing patterns,
mouse movements, timing variations, and natural mistakes.
"""

from __future__ import annotations

import asyncio
import random
import math
import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("pureswarm.tools.humanize")


@dataclass
class TypingProfile:
    """Typing behavior profile - customized to look like a specific person."""

    # Words per minute range (Jay types fast but not robotically)
    wpm_min: int = 55
    wpm_max: int = 85

    # Typo probability (humans make mistakes)
    typo_rate: float = 0.02  # 2% of characters

    # Probability of noticing and fixing typo
    typo_fix_rate: float = 0.85  # 85% get fixed

    # Pause patterns (milliseconds)
    pause_after_word: Tuple[int, int] = (50, 200)
    pause_after_sentence: Tuple[int, int] = (300, 800)
    pause_after_paragraph: Tuple[int, int] = (800, 2000)
    pause_thinking: Tuple[int, int] = (1500, 4000)  # "Hmm, how do I say this..."

    # Burst typing (type fast for a bit, then slow down)
    burst_probability: float = 0.3
    burst_speed_multiplier: float = 1.4

    # Keys that are commonly mistyped together
    adjacent_keys: dict = field(default_factory=lambda: {
        'a': ['s', 'q', 'w', 'z'],
        'b': ['v', 'g', 'h', 'n'],
        'c': ['x', 'd', 'f', 'v'],
        'd': ['s', 'e', 'r', 'f', 'c', 'x'],
        'e': ['w', 's', 'd', 'r'],
        'f': ['d', 'r', 't', 'g', 'v', 'c'],
        'g': ['f', 't', 'y', 'h', 'b', 'v'],
        'h': ['g', 'y', 'u', 'j', 'n', 'b'],
        'i': ['u', 'j', 'k', 'o'],
        'j': ['h', 'u', 'i', 'k', 'm', 'n'],
        'k': ['j', 'i', 'o', 'l', 'm'],
        'l': ['k', 'o', 'p'],
        'm': ['n', 'j', 'k'],
        'n': ['b', 'h', 'j', 'm'],
        'o': ['i', 'k', 'l', 'p'],
        'p': ['o', 'l'],
        'q': ['w', 'a'],
        'r': ['e', 'd', 'f', 't'],
        's': ['a', 'w', 'e', 'd', 'x', 'z'],
        't': ['r', 'f', 'g', 'y'],
        'u': ['y', 'h', 'j', 'i'],
        'v': ['c', 'f', 'g', 'b'],
        'w': ['q', 'a', 's', 'e'],
        'x': ['z', 's', 'd', 'c'],
        'y': ['t', 'g', 'h', 'u'],
        'z': ['a', 's', 'x'],
    })


@dataclass
class MouseProfile:
    """Mouse movement profile - humans don't move in straight lines."""

    # Movement speed variation
    speed_min: float = 0.3  # Slow, deliberate
    speed_max: float = 1.2  # Quick flick

    # Curve intensity (0 = straight, 1 = very curved)
    curve_intensity: float = 0.4

    # Overshoot probability (move past target, then correct)
    overshoot_rate: float = 0.15

    # Micro-movements while "reading" (subtle mouse wiggle)
    idle_wiggle: bool = True
    wiggle_radius: int = 5

    # Occasional random scroll while reading
    random_scroll_rate: float = 0.2


@dataclass
class BehaviorProfile:
    """Overall behavior profile - timing and patterns."""

    # Time spent "reading" content before acting (seconds)
    read_time_per_100_chars: Tuple[float, float] = (0.8, 1.5)

    # Probability of re-reading something
    reread_rate: float = 0.1

    # Break patterns
    micro_break_rate: float = 0.05  # 5% chance of 2-5 second pause
    short_break_rate: float = 0.01  # 1% chance of 10-30 second break

    # Time of day variations (slower at night, faster mid-day)
    apply_time_variations: bool = True

    # Occasionally check other tabs (realistic distraction)
    distraction_rate: float = 0.02


class HumanBehavior:
    """Applies human-like behavior to browser automation."""

    def __init__(self,
                 typing: TypingProfile = None,
                 mouse: MouseProfile = None,
                 behavior: BehaviorProfile = None) -> None:
        self.typing = typing or TypingProfile()
        self.mouse = mouse or MouseProfile()
        self.behavior = behavior or BehaviorProfile()

        # Track state for consistent behavior within a session
        self._fatigue_level = 0.0  # Increases over time, affects speed
        self._actions_count = 0
        self._session_start = None

    async def type_like_human(self, page, selector: str, text: str) -> None:
        """Type text with human-like patterns."""
        element = await page.wait_for_selector(selector, timeout=10000)
        if not element:
            return

        await element.click()
        await self._random_pause(50, 150)  # Small pause after clicking

        typed_text = ""
        i = 0

        while i < len(text):
            char = text[i]

            # Decide typing speed for this character
            base_delay = self._get_typing_delay()

            # Burst typing (occasionally type faster)
            if random.random() < self.typing.burst_probability:
                base_delay /= self.typing.burst_speed_multiplier

            # Should we make a typo?
            if random.random() < self.typing.typo_rate and char.isalpha():
                typo_char = self._get_typo(char)
                await page.keyboard.type(typo_char, delay=base_delay)
                typed_text += typo_char
                await self._random_pause(100, 300)  # Notice the mistake

                # Fix the typo?
                if random.random() < self.typing.typo_fix_rate:
                    await page.keyboard.press("Backspace")
                    await self._random_pause(50, 150)
                    typed_text = typed_text[:-1]
                    # Now type the correct character
                    await page.keyboard.type(char, delay=base_delay)
                    typed_text += char
                else:
                    # Didn't notice, continue
                    i += 1
                    continue

            else:
                # Normal typing
                await page.keyboard.type(char, delay=base_delay)
                typed_text += char

            # Pause after word
            if char == ' ':
                await self._random_pause(*self.typing.pause_after_word)

            # Pause after sentence
            if char in '.!?':
                await self._random_pause(*self.typing.pause_after_sentence)

            # Pause after paragraph/newline
            if char == '\n':
                await self._random_pause(*self.typing.pause_after_paragraph)

            # Occasional thinking pause mid-sentence
            if random.random() < 0.01:  # 1% chance
                await self._random_pause(*self.typing.pause_thinking)

            i += 1

        self._actions_count += 1

    def _get_typing_delay(self) -> int:
        """Calculate delay between keystrokes based on WPM."""
        # Average word is 5 characters, so chars per minute = WPM * 5
        wpm = random.randint(self.typing.wpm_min, self.typing.wpm_max)

        # Apply fatigue (slower over time)
        wpm = int(wpm * (1 - self._fatigue_level * 0.2))

        chars_per_minute = wpm * 5
        ms_per_char = 60000 / chars_per_minute

        # Add variation
        variation = random.uniform(0.7, 1.3)
        return int(ms_per_char * variation)

    def _get_typo(self, char: str) -> str:
        """Get a realistic typo for a character."""
        char_lower = char.lower()
        if char_lower in self.typing.adjacent_keys:
            typo = random.choice(self.typing.adjacent_keys[char_lower])
            return typo.upper() if char.isupper() else typo
        return char  # No adjacent keys defined, no typo

    async def move_mouse_human(self, page, x: int, y: int) -> None:
        """Move mouse with human-like curves and imperfections."""
        # Get current position
        current = await page.evaluate("() => ({x: window.mouseX || 0, y: window.mouseY || 0})")
        start_x, start_y = current.get('x', 0), current.get('y', 0)

        # Calculate distance
        distance = math.sqrt((x - start_x) ** 2 + (y - start_y) ** 2)

        # Number of steps based on distance
        steps = max(10, int(distance / 10))

        # Generate curved path using Bezier-like control points
        control_x = (start_x + x) / 2 + random.uniform(-50, 50) * self.mouse.curve_intensity
        control_y = (start_y + y) / 2 + random.uniform(-50, 50) * self.mouse.curve_intensity

        # Move along path
        for i in range(steps):
            t = i / steps

            # Quadratic Bezier interpolation
            curr_x = (1-t)**2 * start_x + 2*(1-t)*t * control_x + t**2 * x
            curr_y = (1-t)**2 * start_y + 2*(1-t)*t * control_y + t**2 * y

            # Add micro-jitter
            curr_x += random.uniform(-2, 2)
            curr_y += random.uniform(-2, 2)

            await page.mouse.move(curr_x, curr_y)

            # Variable speed
            delay = random.uniform(5, 20) / (self.mouse.speed_min + random.random() * (self.mouse.speed_max - self.mouse.speed_min))
            await asyncio.sleep(delay / 1000)

        # Overshoot and correct?
        if random.random() < self.mouse.overshoot_rate:
            overshoot_x = x + random.uniform(-20, 20)
            overshoot_y = y + random.uniform(-20, 20)
            await page.mouse.move(overshoot_x, overshoot_y)
            await asyncio.sleep(random.uniform(50, 150) / 1000)
            await page.mouse.move(x, y)

        self._actions_count += 1

    async def click_human(self, page, selector: str) -> None:
        """Click with human-like behavior."""
        element = await page.wait_for_selector(selector, timeout=10000)
        if not element:
            return

        # Get element bounds
        box = await element.bounding_box()
        if not box:
            await element.click()
            return

        # Click slightly off-center (humans don't click dead center)
        x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
        y = box['y'] + box['height'] * random.uniform(0.3, 0.7)

        # Move mouse to element
        await self.move_mouse_human(page, int(x), int(y))

        # Small pause before clicking (aiming)
        await self._random_pause(50, 200)

        # Click with slight hold (humans don't instant-click)
        await page.mouse.down()
        await self._random_pause(50, 150)
        await page.mouse.up()

        # Small pause after clicking
        await self._random_pause(100, 300)

        self._actions_count += 1

    async def read_content(self, page, content_length: int = 500) -> None:
        """Simulate reading content on the page."""
        # Calculate read time
        min_time, max_time = self.behavior.read_time_per_100_chars
        read_time = (content_length / 100) * random.uniform(min_time, max_time)

        # Add scroll behavior while "reading"
        scroll_intervals = int(read_time / 2)
        for _ in range(scroll_intervals):
            # Scroll a bit
            if random.random() < 0.7:
                scroll_amount = random.randint(50, 200)
                await page.evaluate(f"window.scrollBy(0, {scroll_amount})")

            # Idle mouse wiggle
            if self.mouse.idle_wiggle and random.random() < 0.3:
                await page.mouse.move(
                    random.randint(-self.mouse.wiggle_radius, self.mouse.wiggle_radius),
                    random.randint(-self.mouse.wiggle_radius, self.mouse.wiggle_radius)
                )

            await asyncio.sleep(random.uniform(0.5, 2))

        # Re-read? Scroll back up occasionally
        if random.random() < self.behavior.reread_rate:
            await page.evaluate("window.scrollBy(0, -300)")
            await asyncio.sleep(random.uniform(1, 3))

    async def take_break(self) -> None:
        """Simulate natural breaks."""
        if random.random() < self.behavior.micro_break_rate:
            logger.debug("Taking micro-break")
            await asyncio.sleep(random.uniform(2, 5))
        elif random.random() < self.behavior.short_break_rate:
            logger.debug("Taking short break")
            await asyncio.sleep(random.uniform(10, 30))

    async def _random_pause(self, min_ms: int, max_ms: int) -> None:
        """Random pause in milliseconds."""
        await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000)

    def increase_fatigue(self, amount: float = 0.01) -> None:
        """Increase fatigue level (affects typing speed, etc.)."""
        self._fatigue_level = min(1.0, self._fatigue_level + amount)

    def reset_fatigue(self) -> None:
        """Reset fatigue (after a break)."""
        self._fatigue_level = 0.0


# Pre-configured profiles
JAY_TYPING = TypingProfile(
    wpm_min=60,
    wpm_max=90,
    typo_rate=0.015,  # Jay is pretty accurate
    typo_fix_rate=0.9,  # Usually catches mistakes
)

JAY_MOUSE = MouseProfile(
    speed_min=0.4,
    speed_max=1.0,
    curve_intensity=0.35,
    overshoot_rate=0.1,
)

JAY_BEHAVIOR = BehaviorProfile(
    read_time_per_100_chars=(0.6, 1.2),  # Reads fairly fast
    reread_rate=0.08,
    micro_break_rate=0.03,
)


def create_jay_profile() -> HumanBehavior:
    """Create a behavior profile that mimics Jay's patterns."""
    return HumanBehavior(
        typing=JAY_TYPING,
        mouse=JAY_MOUSE,
        behavior=JAY_BEHAVIOR
    )
