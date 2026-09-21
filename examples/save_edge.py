"""Prepare and optionally persist an Impact relationship through GLPI's UI.

A real save is refused unless GLPI computeDelta() contains the expected edge.
Successful persistence is reported only if the edge remains after reopening the
Impact workspace.
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
        navigator = ImpactNavigator(session.page, required("GLPI_URL"))
        navigator.open_impact(source.itemtype, source.items_id)
        builder = ImpactBuilder(session.page)
        result = builder.add_edge_to_workspace(edge)
        created = bool(result["created"])
        delta_detected = bool(result["delta_detected"])

        if confirm and not delta_detected:
            raise SystemExit(
                "Refusing save: GLPI computeDelta() does not contain the expected edge. "
                "Run examples/inspect_edge_runtime.py and reproduce GLPI's native edge flow."
            )

        save_result = ImpactPersistence(session.page, builder).save(
            confirm=confirm,
            expected_edge=edge if confirm else None,
            reload_workspace=(
                lambda: navigator.open_impact(source.itemtype, source.items_id)
                if confirm else None
            ),
        )
        persisted = save_result.persisted
        print(json.dumps({
            "edge": edge.id,
            "created_in_workspace": created,
            "glpi_delta_detected": delta_detected,
            "save_confirmed": confirm,
            "save_attempted": save_result.attempted,
            "persisted": save_result.persisted,
            "verification": save_result.verification,
            "delta_cleared": save_result.delta_cleared,
            "reloaded_edge_present": save_result.reloaded_edge_present,
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
