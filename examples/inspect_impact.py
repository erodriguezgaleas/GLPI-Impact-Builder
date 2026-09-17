"""Inspect a live GLPI Impact workspace without persisting changes.

Environment variables:
    GLPI_URL       Base URL of the GLPI instance.
    GLPI_ITEMTYPE  Item type to open, defaults to Computer.
    GLPI_ITEM_ID   Item ID to inspect.
    GLPI_STATE     Optional Playwright storage-state JSON path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from glpiimpact.browser import BrowserManager, BrowserOptions
from glpiimpact.impact.builder import ImpactBuilder
from glpiimpact.impact.inspector import ImpactInspector
from glpiimpact.impact.navigator import ImpactNavigator


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    base_url = required("GLPI_URL")
    itemtype = os.getenv("GLPI_ITEMTYPE", "Computer")
    items_id = int(required("GLPI_ITEM_ID"))
    state = os.getenv("GLPI_STATE")

    options = BrowserOptions(
        headless=False,
        storage_state=Path(state) if state else None,
    )
    browser = BrowserManager(options)
    try:
        session = browser.start()
        navigator = ImpactNavigator(session.page, base_url)
        navigator.open_impact(itemtype, items_id)

        builder = ImpactBuilder(session.page)
        inspector = ImpactInspector(session.page)
        report = {
            "constants": builder.constants(),
            "nodes": builder.nodes(),
            "edges": builder.edges(),
            "delta": builder.compute_delta(),
            "runtime": inspector.describe(),
            "save_candidates": inspector.save_candidates(),
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
    finally:
        browser.stop()


if __name__ == "__main__":
    main()
