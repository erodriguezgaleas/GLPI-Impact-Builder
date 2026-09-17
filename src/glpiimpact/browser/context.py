"""Playwright BrowserContext wrapper."""

from playwright.sync_api import BrowserContext

class ContextManager:
    """Helper around a Playwright BrowserContext."""

    def __init__(self, context: BrowserContext):
        self.context = context

    def cookies(self):
        return self.context.cookies()

    def clear_cookies(self):
        self.context.clear_cookies()

    def storage_state(self):
        return self.context.storage_state()
