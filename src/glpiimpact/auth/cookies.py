"""Cookie and Playwright storage-state persistence for GLPI sessions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext


class CookieManager:
    """Persist and restore browser authentication state.

    Playwright's storage state contains cookies and origin-local storage and is
    therefore preferable to persisting cookies alone when a GLPI deployment
    uses additional browser-side authentication state.
    """

    def __init__(self, context: BrowserContext):
        self.context = context

    def cookies(self) -> list[dict[str, Any]]:
        """Return cookies from the active browser context."""
        return self.context.cookies()

    def clear(self) -> None:
        """Remove all cookies from the active browser context."""
        self.context.clear_cookies()

    def save_storage_state(self, path: str | Path) -> Path:
        """Persist the complete Playwright storage state as JSON."""
        destination = Path(path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.context.storage_state(path=str(destination))
        return destination

    def load_storage_state(self, path: str | Path) -> dict[str, Any]:
        """Read a previously persisted storage-state file.

        The returned dictionary can be passed to ``browser.new_context`` via
        its ``storage_state`` argument. Existing BrowserContext objects cannot
        replace their complete storage state in place.
        """
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Storage state not found: {source}")

        with source.open("r", encoding="utf-8") as handle:
            state = json.load(handle)

        if not isinstance(state, dict):
            raise ValueError("Invalid Playwright storage-state document")
        return state

    def restore_cookies(self, path: str | Path) -> int:
        """Restore the cookie portion of a saved Playwright storage state."""
        state = self.load_storage_state(path)
        cookies = state.get("cookies", [])
        if not isinstance(cookies, list):
            raise ValueError("Invalid cookies entry in Playwright storage state")
        if cookies:
            self.context.add_cookies(cookies)
        return len(cookies)
