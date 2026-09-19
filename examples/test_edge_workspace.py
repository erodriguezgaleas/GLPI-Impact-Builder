"""Test an Impact relationship in the browser workspace without saving it.

Defaults model the reverse-engineering case Computer::15 -> Computer::16.
The report explicitly distinguishes a Cytoscape edge from a GLPI-recognized
pending delta. This script NEVER clicks Save.
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


def delta_contains_edge(delta: dict, edge: ImpactEdge) -> bool:
    source_id = str(edge.source.items_id)
    target_id = str(edge.impacted.items_id)

    def walk(value) -> bool:
        if isinstance(value, dict):
            if edge.id in value:
                return True
            if (
                str(value.get("items_id_source")) == source_id
                and str(value.get("items_id_impacted")) == target_id
                and value.get("itemtype_source") == edge.source.itemtype
                and value.get("itemtype_impacted") == edge.impacted.itemtype
            ):
                return True
            return any(walk(item) for item in value.values())
        if isinstance(value, list):
            return any(walk(item) for item in value)
        return False

    return walk(delta)


def main() -> None:
    base_url = required("GLPI_URL")
    source = ImpactNode(os.getenv("GLPI_SOURCE_TYPE", "Computer"), int(os.getenv("GLPI_SOURCE_ID", "15")))
    target = ImpactNode(os.getenv("GLPI_TARGET_TYPE", "Computer"), int(os.getenv("GLPI_TARGET_ID", "16")))
    edge = ImpactEdge(source, target)
    state = os.getenv("GLPI_STATE")

    browser = BrowserManager(BrowserOptions(headless=False, storage_state=Path(state) if state else None))
    created = False
    try:
        session = browser.start()
        ImpactNavigator(session.page, base_url).open_impact(source.itemtype, source.items_id)
        builder = ImpactBuilder(session.page)

        before = builder.compute_delta()
        result = builder.add_edge_to_workspace(edge)
        created = bool(result["created"])
        after = result["delta"]
        detected = delta_contains_edge(after, edge)

        print(json.dumps({
            "edge": edge.id,
            "source_present": builder.has_node(source),
            "target_present": builder.has_node(target),
            "created_in_cytoscape": created,
            "glpi_delta_detected": detected,
            "native_edge_flow_required": created and not detected,
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
