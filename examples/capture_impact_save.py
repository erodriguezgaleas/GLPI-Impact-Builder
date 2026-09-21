"""Capture one manually performed GLPI Impact save for endpoint discovery.

The script does not create or save anything itself. After the Impact workspace
opens, perform exactly one known Save operation in GLPI, then return here and
press Enter. Captured XHR/fetch evidence is redacted before it is written.
"""

from __future__ import annotations
import os
from pathlib import Path
from glpiimpact.browser import BrowserManager, BrowserOptions
from glpiimpact.impact import ImpactNavigator
from glpiimpact.impact.network import ImpactNetworkRecorder


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
    output = Path(os.getenv("GLPI_CAPTURE_PATH", "impact-network-capture.json"))

    browser = BrowserManager(BrowserOptions(
        headless=False,
        storage_state=Path(state) if state else None,
    ))
    try:
        session = browser.start()
        ImpactNavigator(session.page, base_url).open_impact(itemtype, items_id)
        recorder = ImpactNetworkRecorder(session.page, impact_only=False).start()
        input("Perform exactly one known Save operation in the opened GLPI browser, then press Enter here: ")
        recorder.stop()
        saved = recorder.export_json(output)
        print(f"Redacted capture saved locally: {saved}")
        print(f"Captured XHR/fetch requests: {len(recorder.requests)}")
        print(f"Successful write responses: {len(recorder.successful_write_responses())}")
    finally:
        browser.stop()


if __name__ == "__main__":
    main()
