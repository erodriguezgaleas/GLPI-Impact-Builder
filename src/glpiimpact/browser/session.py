"""Browser session wrapper around a Playwright Page."""

from playwright.sync_api import Page

class BrowserSession:
    """Lightweight wrapper exposing common page operations."""

    def __init__(self, page: Page):
        self.page = page

    def goto(self, url: str):
        return self.page.goto(url)

    def html(self) -> str:
        return self.page.content()

    def screenshot(self, path: str):
        self.page.screenshot(path=path)

    def close(self):
        self.page.close()
