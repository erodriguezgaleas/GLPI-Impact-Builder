"""Create a local Playwright storage-state file after GLPI login.

Credentials are read from environment variables and are never printed.
The generated state file is excluded by the repository .gitignore.
"""

from __future__ import annotations

import os
from pathlib import Path

from glpiimpact.auth import CookieManager, LoginManager
from glpiimpact.browser import BrowserManager, BrowserOptions


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    destination = Path(os.getenv("GLPI_STATE", ".glpi-storage-state.json"))
    browser = BrowserManager(BrowserOptions(headless=False))
    try:
        LoginManager(browser).login(
            required("GLPI_URL"),
            required("GLPI_USERNAME"),
            required("GLPI_PASSWORD"),
        )
        if browser.context is None:
            raise RuntimeError("Browser context was not created")
        saved = CookieManager(browser.context).save_storage_state(destination)
        print(f"Authenticated storage state saved locally: {saved}")
    finally:
        browser.stop()


if __name__ == "__main__":
    main()
