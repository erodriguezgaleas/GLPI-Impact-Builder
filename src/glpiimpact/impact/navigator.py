"""Navigation helpers for opening GLPI Impact workspaces."""

from __future__ import annotations

from urllib.parse import urlencode, urljoin

from playwright.sync_api import Page


class ImpactNavigator:
    """Open an item's Impact view and wait for the GLPIImpact runtime."""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/") + "/"

    def item_url(self, itemtype: str, items_id: int) -> str:
        """Build the standard GLPI item URL used as the navigation anchor."""
        script = f"front/{itemtype.lower()}.form.php"
        return urljoin(self.base_url, script) + "?" + urlencode({"id": items_id})

    def open_item(self, itemtype: str, items_id: int):
        return self.page.goto(self.item_url(itemtype, items_id))

    def open_impact(
        self,
        itemtype: str,
        items_id: int,
        *,
        timeout: int = 30_000,
    ) -> None:
        """Open an item and select its Impact tab using resilient UI signals.

        GLPI versions and translations can use different tab labels, so this
        tries accessible labels first and href/content hints second.
        """
        self.open_item(itemtype, items_id)

        candidates = [
            self.page.get_by_role("tab", name="Impact", exact=True),
            self.page.get_by_role("link", name="Impact", exact=True),
            self.page.locator("a[href*='impact']"),
            self.page.locator("[data-bs-target*='impact']"),
        ]
        for locator in candidates:
            try:
                if locator.count() and locator.first.is_visible():
                    locator.first.click()
                    break
            except Exception:
                continue

        self.page.wait_for_function(
            "() => Boolean(window.GLPIImpact && GLPIImpact.cy)",
            timeout=timeout,
        )
