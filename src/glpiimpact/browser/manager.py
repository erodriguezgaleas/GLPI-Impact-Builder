"""Browser manager for Playwright lifecycle."""

from playwright.sync_api import sync_playwright

from .context import ContextManager
from .options import BrowserOptions
from .session import BrowserSession


class BrowserManager:
    """Manage Playwright browser, context and page lifecycle."""

    def __init__(self, options: BrowserOptions):
        self.options = options
        self._playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self) -> BrowserSession:
        if self.page is not None:
            return BrowserSession(self.page)

        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(
            headless=self.options.headless,
            slow_mo=self.options.slow_mo,
        )

        context_options = {
            "accept_downloads": self.options.accept_downloads,
            "viewport": {
                "width": self.options.viewport_width,
                "height": self.options.viewport_height,
            },
        }
        storage_state = self.options.storage_state
        if storage_state is not None:
            storage_path = storage_state.expanduser().resolve()
            if storage_path.is_file():
                context_options["storage_state"] = str(storage_path)

        self.context = self.browser.new_context(**context_options)
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.options.timeout)
        return BrowserSession(self.page)

    def get_context(self) -> ContextManager:
        if self.context is None:
            raise RuntimeError("Browser has not been started")
        return ContextManager(self.context)

    def stop(self) -> None:
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
        self.page = None
        self.context = None
        self.browser = None
        self._playwright = None
