"""
Browserbase session factory.

If BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID are set, each create_remote_session()
call provisions a new cloud session and returns a Playwright Browser connected over CDP.
Otherwise, falls back to launching a local headless Chromium.
"""

import logging
import os
from typing import Any

from playwright.async_api import Browser, Playwright

logger = logging.getLogger(__name__)

_BB_API = "https://www.browserbase.com/v1"


def is_configured() -> bool:
    return bool(os.environ.get("BROWSERBASE_API_KEY")) and bool(
        os.environ.get("BROWSERBASE_PROJECT_ID")
    )


async def create_remote_session(playwright: Playwright) -> tuple[Browser, str | None]:
    """
    Return (browser, browserbase_session_id).
    session_id is None when running in local mode.
    """
    if is_configured():
        return await _connect_browserbase(playwright)
    return await _launch_local(playwright), None


async def _connect_browserbase(playwright: Playwright) -> tuple[Browser, str]:
    import httpx

    api_key = os.environ["BROWSERBASE_API_KEY"]
    project_id = os.environ["BROWSERBASE_PROJECT_ID"]

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_BB_API}/sessions",
            headers={"X-BB-API-Key": api_key, "Content-Type": "application/json"},
            json={"projectId": project_id},
        )
        resp.raise_for_status()
        data = resp.json()

    session_id: str = data["id"]
    connect_url: str = data["connectUrl"]

    browser = await playwright.chromium.connect_over_cdp(connect_url)
    logger.info("Connected to Browserbase session %s", session_id)
    return browser, session_id


async def _launch_local(playwright: Playwright) -> Browser:
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
    )
    logger.info("Local Chromium launched")
    return browser
