"""Strudel.cc browser automation integration with resilient fallbacks."""

from __future__ import annotations

import logging
import random
from typing import Any

logger = logging.getLogger(__name__)


class StrudelClient:
    """Controls Strudel via Playwright when possible."""

    def __init__(self, base_url: str = "https://strudel.cc", headless: bool = True) -> None:
        self.base_url = base_url
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._page = None

    async def start(self) -> None:
        """Start browser automation session."""

        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._page = await self._browser.new_page()
            await self._page.goto(self.base_url, wait_until="networkidle")
            logger.info("Connected to Strudel at %s", self.base_url)
        except Exception as exc:
            logger.warning("Could not initialize Strudel browser automation: %s", exc)
            await self.stop()

    async def stop(self) -> None:
        """Stop browser session if active."""

        try:
            if self._browser is not None:
                await self._browser.close()
            if self._playwright is not None:
                await self._playwright.stop()
        finally:
            self._playwright = None
            self._browser = None
            self._page = None

    async def set_pattern(self, pattern: str) -> bool:
        """Inject a pattern into the Strudel editor and trigger play."""

        if self._page is None:
            logger.warning("Strudel page not available; skipping set_pattern.")
            return False

        script = """
        (pattern) => {
            const editor = document.querySelector('.cm-content');
            if (!editor) return false;
            editor.innerHTML = '';
            editor.textContent = pattern;
            editor.dispatchEvent(new Event('input', { bubbles: true }));
            const playButton = [...document.querySelectorAll('button')].find(b => /play/i.test(b.innerText));
            if (playButton) playButton.click();
            return true;
        }
        """
        try:
            ok = await self._page.evaluate(script, pattern)
            if not ok:
                logger.warning("Strudel editor not found. Pattern generated but not injected.")
            return bool(ok)
        except Exception as exc:
            logger.warning("Failed to set Strudel pattern: %s", exc)
            return False

    def generate_pattern(self, context: dict[str, Any]) -> str:
        """Create simple evolving patterns based on requested mood."""

        mood = str(context.get("mood", "ambient"))
        mood_map = {
            "ambient": 'note("c3 e3 g3 b3").slow(2).s("sine").room(0.8)',
            "eerie": 'note("c2 eb2 gb2").slow(3).s("triangle").lpf(600).room(0.9)',
            "glitchy": 'n("0 3 7 10").s("square").fast(4).degradeBy(0.3)',
            "sparse": 'note("c2 ~ ~ g2").slow(4).s("sawtooth").gain(0.5)',
            "ritualistic": 'stack(note("c2 c3").slow(2), note("g2 bb2").slow(3)).room(0.85)',
        }
        chosen = mood_map.get(mood, random.choice(list(mood_map.values())))
        return f"// mood={mood}\n{chosen}"
