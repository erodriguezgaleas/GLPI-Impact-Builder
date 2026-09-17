"""Browser manager for Playwright lifecycle."""

from playwright.sync_api import sync_playwright

from .options import BrowserOptions
from .session import BrowserSession
from .context import ContextManager


class BrowserManager:
    """Manages Playwright browser, context and page lifecycle."""

    def __init__(self, options: BrowserOptions):
        self.options = options
        self._playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self) -> BrowserSession:
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(
            headless=self.options.headless,
            slow_mo=self.options.slow_mo,
        )
        self.context = self.browser.new_context(
            accept_downloads=self.options.accept_downloads,
            viewport={
                "width": self.options.viewport_width,
                "height": self.options.viewport_height,
            },
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.options.timeout)
        return BrowserSession(self.page)

    def get_context(self) -> ContextManager:
        return ContextManager(self.context)

    def stop(self):
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
