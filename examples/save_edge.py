"""Prepare and optionally persist an Impact relationship through GLPI's UI.

Defaults to Computer::15 -> Computer::16. It is a dry run unless
GLPI_CONFIRM_SAVE is exactly YES. No direct private AJAX endpoint is used.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from glpiimpact.browser import BrowserManager, BrowserOptions
from glpiimpact.impact import ImpactBuilder, ImpactEdge, ImpactNavigator, ImpactNode
from glpiimpact.impact.persistence import ImpactPersistence


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    source = ImpactNode(os.getenv("GLPI_SOURCE_TYPE", "Computer"), int(os.getenv("GLPI_SOURCE_ID", "15")))
    target = ImpactNode(os.getenv("GLPI_TARGET_TYPE", "Computer"), int(os.getenv("GLPI_TARGET_ID", "16")))
    edge = ImpactEdge(source, target)
    confirm = os.getenv("GLPI_CONFIRM_SAVE") == "YES"
    state = os.getenv("GLPI_STATE")

    browser = BrowserManager(BrowserOptions(headless=False, storage_state=Path(state) if state else None))
    created = False
    persisted = False
    try:
        session = browser.start()
        ImpactNavigator(session.page, required("GLPI_URL")).open_impact(source.itemtype, source.items_id)
        builder = ImpactBuilder(session.page)
        result = builder.add_edge_to_workspace(edge)
        created = bool(result["created"])

        save_result = ImpactPersistence(session.page, builder).save(confirm=confirm)
        persisted = save_result.persisted
        print(json.dumps({
            "edge": edge.id,
            "created_in_workspace": created,
            "save_confirmed": confirm,
            "save_attempted": save_result.attempted,
            "persisted": save_result.persisted,
            "delta_before_save": save_result.delta_before,
            "delta_after_save": save_result.delta_after,
            "captured_requests": save_result.requests,
        }, indent=2, ensure_ascii=False))
    finally:
        if browser.page is not None and created and not persisted:
            try:
                ImpactBuilder(browser.page).remove_workspace_element(edge.id)
            except Exception:
                pass
        browser.stop()


if __name__ == "__main__":
    main()
