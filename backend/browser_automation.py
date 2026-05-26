import base64
import logging
import uuid
from datetime import datetime
from typing import Any

from playwright.async_api import async_playwright, Browser, BrowserContext

from backend.browserbase_session import create_remote_session, is_configured

logger = logging.getLogger(__name__)


class BrowserAutomation:
    def __init__(self) -> None:
        self.playwright = None
        self._shared_browser: Browser | None = None  # used in local mode only
        # session_id -> {browser?, context, page, url, bb_session_id?, created_at}
        self.sessions: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        self.playwright = await async_playwright().start()
        if not is_configured():
            # Pre-launch one shared local browser; Browserbase sessions are created per-call
            self._shared_browser = await self.playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox",
                      "--disable-dev-shm-usage", "--disable-gpu"],
            )
        mode = "Browserbase" if is_configured() else "local Chromium"
        logger.info("Browser automation initialized in %s mode", mode)

    async def create_session(self, url: str) -> str:
        if not self.playwright:
            raise RuntimeError("BrowserAutomation not initialized")

        browser, bb_session_id = await create_remote_session(self.playwright)

        # Browserbase returns a connected browser; local returns a fresh launch
        if is_configured():
            ctx: BrowserContext = browser.contexts[0] if browser.contexts else await browser.new_context()
        else:
            ctx = await self._shared_browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )

        page = await ctx.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "browser": browser if is_configured() else None,
            "context": ctx,
            "page": page,
            "url": url,
            "bb_session_id": bb_session_id,
            "created_at": datetime.now(),
        }
        logger.info("Session created: %s -> %s", session_id, url)
        return session_id

    async def close_session(self, session_id: str) -> None:
        session = self.sessions.pop(session_id, None)
        if not session:
            return
        try:
            await session["context"].close()
            if session.get("browser"):  # per-session browser (Browserbase)
                await session["browser"].close()
        except Exception as exc:
            logger.warning("Error closing session %s: %s", session_id, exc)

    async def execute_command(
        self, session_id: str, command: dict[str, Any]
    ) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        page = session["page"]
        action = command.get("action_type") or command.get("command", "unknown")

        if action == "navigate":
            url = command.get("target") or command.get("value", "about:blank")
            if not url.startswith("http"):
                url = f"https://{url}"
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return {"url": url, "title": await page.title()}

        if action == "click":
            selector = command.get("target", "button")
            await page.click(selector, timeout=10000)
            return {"selector": selector}

        if action == "type":
            selector = command.get("target", "input")
            text = command.get("value") or command.get("params", {}).get("text", "")
            await page.fill(selector, text)
            return {"selector": selector, "text": text}

        if action == "scroll":
            direction = command.get("direction", "down")
            amounts = {"down": (0, 500), "up": (0, -500), "left": (-500, 0), "right": (500, 0)}
            dx, dy = amounts.get(direction, (0, 500))
            await page.evaluate(f"window.scrollBy({dx}, {dy})")
            return {"direction": direction}

        if action in ("wait",):
            ms = int(command.get("duration", 1)) * 1000
            await page.wait_for_timeout(ms)
            return {"waited_ms": ms}

        if action == "extract":
            description = command.get("description") or command.get("target", "page content")
            from backend.perception import filter_tree
            nodes, before, after = await filter_tree(page, description)
            savings = round((1 - after / max(before, 1)) * 100)
            return {
                "nodes": nodes[:50],   # cap response size
                "tokens_before": before,
                "tokens_after": after,
                "token_savings_pct": savings,
            }

        if action in ("back",):
            await page.go_back()
            return {"url": page.url}

        if action in ("forward",):
            await page.go_forward()
            return {"url": page.url}

        if action in ("refresh",):
            await page.reload()
            return {"url": page.url, "title": await page.title()}

        if action in ("screenshot",):
            return {"screenshot": await self._screenshot_b64(page)}

        raise ValueError(f"Unknown action: {action}")

    async def take_screenshot(self, session_id: str) -> str:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        return await self._screenshot_b64(session["page"])

    async def _screenshot_b64(self, page) -> str:
        data = await page.screenshot(full_page=False)
        return base64.b64encode(data).decode()

    async def get_page_info(self, session_id: str) -> dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        page = session["page"]
        return {"url": page.url, "title": await page.title()}

    async def cleanup(self) -> None:
        for session_id in list(self.sessions):
            await self.close_session(session_id)
        if self._shared_browser:
            await self._shared_browser.close()
        if self.playwright:
            await self.playwright.stop()

    def get_session_count(self) -> int:
        return len(self.sessions)
