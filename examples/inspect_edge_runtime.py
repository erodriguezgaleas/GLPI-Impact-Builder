"""Dump GLPIImpact runtime evidence relevant to native edge creation.

Read-only: this script does not add nodes, edges or persist changes.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from glpiimpact.browser import BrowserManager, BrowserOptions
from glpiimpact.impact import ImpactInspector, ImpactNavigator


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
    output = Path(os.getenv("GLPI_RUNTIME_REPORT_PATH", "impact-runtime-report.json"))

    browser = BrowserManager(BrowserOptions(
        headless=False,
        storage_state=Path(state) if state else None,
    ))
    try:
        session = browser.start()
        ImpactNavigator(session.page, base_url).open_impact(itemtype, items_id)
        report = ImpactInspector(session.page).edge_runtime_report()
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({
            "report": str(output.resolve()),
            "method_count": len(report["runtime"]["methods"]),
            "related_method_count": len(report["related_methods"]),
            "related_method_names": [item["name"] for item in report["related_methods"]],
            "save_candidate_count": len(report["save_candidates"]),
        }, indent=2, ensure_ascii=False))
    finally:
        browser.stop()


if __name__ == "__main__":
    main()
