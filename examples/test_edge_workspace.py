"""Test an Impact relationship in the browser workspace without saving it.

Defaults model the reverse-engineering case Computer::15 -> Computer::16.
Override every value through environment variables when testing another map.

Required:
    GLPI_URL
Optional:
    GLPI_STATE=.glpi-storage-state.json
    GLPI_SOURCE_TYPE=Computer
    GLPI_SOURCE_ID=15
    GLPI_TARGET_TYPE=Computer
    GLPI_TARGET_ID=16

This script NEVER clicks Save and removes the temporary edge before exiting.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from glpiimpact.browser import BrowserManager, BrowserOptions
from glpiimpact.impact import ImpactBuilder, ImpactEdge, ImpactNavigator, ImpactNode


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    base_url = required("GLPI_URL")
    source = ImpactNode(
        os.getenv("GLPI_SOURCE_TYPE", "Computer"),
        int(os.getenv("GLPI_SOURCE_ID", "15")),
    )
    target = ImpactNode(
        os.getenv("GLPI_TARGET_TYPE", "Computer"),
        int(os.getenv("GLPI_TARGET_ID", "16")),
    )
    edge = ImpactEdge(source, target)
    state = os.getenv("GLPI_STATE")

    browser = BrowserManager(
        BrowserOptions(
            headless=False,
            storage_state=Path(state) if state else None,
        )
    )
    created = False
    try:
        session = browser.start()
        ImpactNavigator(session.page, base_url).open_impact(
            source.itemtype, source.items_id
        )
        builder = ImpactBuilder(session.page)

        before = builder.compute_delta()
        result = builder.add_edge_to_workspace(edge)
        created = bool(result["created"])
        after = result["delta"]

        print(json.dumps({
            "edge": edge.id,
            "source_present": builder.has_node(source),
            "target_present": builder.has_node(target),
            "created": created,
            "delta_before": before,
            "delta_after": after,
        }, indent=2, ensure_ascii=False))
    finally:
        if browser.page is not None and created:
            try:
                ImpactBuilder(browser.page).remove_workspace_element(edge.id)
            except Exception:
                pass
        browser.stop()


if __name__ == "__main__":
    main()
