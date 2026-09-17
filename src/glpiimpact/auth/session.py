"""Authenticated GLPI browser-session coordination."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

from ..browser.manager import BrowserManager
from ..browser.session import BrowserSession
from .cookies import CookieManager
from .csrf import CsrfManager


@dataclass
class AuthenticatedSession:
    """Coordinate browser state, authentication persistence and CSRF access."""

    browser: BrowserManager
    base_url: str
    session: BrowserSession | None = None

    def start(self) -> BrowserSession:
        if self.session is None:
            self.session = self.browser.start()
        return self.session

    @property
    def page(self):
        return self.start().page

    @property
    def cookies(self) -> CookieManager:
        if self.browser.context is None:
            self.start()
        return CookieManager(self.browser.context)

    @property
    def csrf(self) -> CsrfManager:
        return CsrfManager(self.page)

    def goto(self, path: str = "/"):
        """Navigate to a path relative to the configured GLPI base URL."""
        base = self.base_url.rstrip("/") + "/"
        return self.page.goto(urljoin(base, path.lstrip("/")))

    def save(self, path: str | Path) -> Path:
        """Persist the authenticated Playwright storage state."""
        return self.cookies.save_storage_state(path)

    def close(self) -> None:
        self.browser.stop()
        self.session = None
