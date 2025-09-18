import base64
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Browser

logger = logging.getLogger(__name__)

class BrowserAutomation:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.sessions: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize Playwright browser automation"""
        try:
            self.playwright = await async_playwright().start()
            # Use Chromium for better compatibility
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            logger.info("Browser automation initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser automation: {e}")
            raise

    async def create_session(self, url: str) -> str:
        """Create a new browser session"""
        try:
            if not self.browser:
                raise Exception("Browser not initialized")
            
            session_id = str(uuid.uuid4())
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = await context.new_page()
            
            # Navigate to the URL
            await page.goto(url, wait_until='networkidle')
            
            self.sessions[session_id] = {
                'context': context,
                'page': page,
                'url': url,
                'created_at': datetime.now()
            }
            
            logger.info(f"Browser session created: {session_id} for {url}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create browser session: {e}")
            raise

    async def close_session(self, session_id: str):
        """Close a browser session"""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                await session['context'].close()
                del self.sessions[session_id]
                logger.info(f"Browser session closed: {session_id}")
            else:
                logger.warning(f"Session not found: {session_id}")
        except Exception as e:
            logger.error(f"Failed to close browser session {session_id}: {e}")
            raise

    async def execute_command(self, session_id: str, command: Dict[str, Any]) -> Any:
        """Execute a browser automation command"""
        try:
            if session_id not in self.sessions:
                raise Exception(f"Session not found: {session_id}")
            
            session = self.sessions[session_id]
            page = session['page']
            command_type = command.get('command')
            
            if command_type == 'navigate':
                url = command.get('target', 'https://www.google.com')
                await page.goto(url, wait_until='networkidle')
                return {'url': url, 'title': await page.title()}
            
            elif command_type == 'click':
                selector = command.get('target', 'button')
                await page.click(selector)
                return {'selector': selector, 'action': 'clicked'}
            
            elif command_type == 'type':
                selector = command.get('target', 'input')
                text = command.get('value', '')
                await page.fill(selector, text)
                return {'selector': selector, 'text': text, 'action': 'typed'}
            
            elif command_type == 'wait':
                duration = command.get('duration', 1)
                await asyncio.sleep(duration)
                return {'duration': duration, 'action': 'waited'}
            
            elif command_type == 'scroll':
                direction = command.get('direction', 'down')
                if direction == 'down':
                    await page.evaluate('window.scrollBy(0, 500)')
                elif direction == 'up':
                    await page.evaluate('window.scrollBy(0, -500)')
                elif direction == 'left':
                    await page.evaluate('window.scrollBy(-500, 0)')
                elif direction == 'right':
                    await page.evaluate('window.scrollBy(500, 0)')
                return {'direction': direction, 'action': 'scrolled'}
            
            else:
                raise Exception(f"Unknown command: {command_type}")
                
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise

    async def take_screenshot(self, session_id: str) -> str:
        """Take a screenshot of the current page"""
        try:
            if session_id not in self.sessions:
                raise Exception(f"Session not found: {session_id}")
            
            session = self.sessions[session_id]
            page = session['page']
            
            # Take screenshot
            screenshot_bytes = await page.screenshot(full_page=True)
            
            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            logger.info(f"Screenshot captured for session: {session_id}")
            return screenshot_base64
            
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            raise

    async def get_page_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about the current page"""
        try:
            if session_id not in self.sessions:
                raise Exception(f"Session not found: {session_id}")
            
            session = self.sessions[session_id]
            page = session['page']
            
            return {
                'url': page.url,
                'title': await page.title(),
                'viewport': await page.viewport_size()
            }
            
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            raise

    async def cleanup(self):
        """Cleanup all browser resources"""
        try:
            # Close all sessions
            for session_id in list(self.sessions.keys()):
                await self.close_session(session_id)
            
            # Close browser
            if self.browser:
                await self.browser.close()
            
            # Stop playwright
            if self.playwright:
                await self.playwright.stop()
            
            logger.info("Browser automation cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def get_session_count(self) -> int:
        """Get the number of active sessions"""
        return len(self.sessions)
