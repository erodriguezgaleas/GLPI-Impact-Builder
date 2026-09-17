"""Browser-backed adapter for the GLPIImpact JavaScript workspace."""

from __future__ import annotations

from typing import Any

from playwright.sync_api import Page

from .graph import ImpactEdge, ImpactNode


class ImpactBuilder:
    """Interact with the GLPI Impact workspace through the browser page.

    This adapter deliberately uses the GLPIImpact object already loaded by the
    GLPI UI instead of reproducing GLPI Cloud's private AJAX implementation.
    """

    def __init__(self, page: Page):
        self.page = page

    def wait_until_ready(self, timeout: int = 30_000) -> None:
        """Wait until GLPIImpact and its Cytoscape instance are available."""
        self.page.wait_for_function(
            "() => Boolean(window.GLPIImpact && GLPIImpact.cy)",
            timeout=timeout,
        )

    def is_ready(self) -> bool:
        return bool(
            self.page.evaluate(
                "() => Boolean(window.GLPIImpact && GLPIImpact.cy)"
            )
        )

    def constants(self) -> dict[str, Any]:
        """Return the known numeric GLPIImpact constants from the live page."""
        names = [
            "NODE", "EDGE", "DEFAULT", "FORWARD", "BACKWARD", "BOTH",
            "EDITION_DEFAULT", "EDITION_ADD_NODE", "EDITION_ADD_EDGE",
            "EDITION_DELETE", "EDITION_ADD_COMPOUND", "EDITION_SETTINGS",
            "DELTA_ACTION_ADD", "DELTA_ACTION_UPDATE", "DELTA_ACTION_DELETE",
            "ACTION_MOVE", "ACTION_ADD_NODE", "ACTION_ADD_EDGE",
            "ACTION_ADD_COMPOUND", "ACTION_ADD_GRAPH", "ACTION_EDIT_COMPOUND",
            "ACTION_REMOVE_FROM_COMPOUND", "ACTION_DELETE",
            "ACTION_EDIT_MAX_DEPTH", "ACTION_EDIT_IMPACT_VISIBILITY",
            "ACTION_EDIT_DEPENDS_VISIBILITY", "ACTION_EDIT_DEPENDS_COLOR",
            "ACTION_EDIT_IMPACT_COLOR", "ACTION_EDIT_IMPACT_AND_DEPENDS_COLOR",
            "ACTION_EDIT_EDGE", "DEFAULT_DEPTH", "MAX_DEPTH", "NO_DEPTH_LIMIT",
            "NODE_ID_SEPERATOR", "EDGE_ID_SEPERATOR",
        ]
        return self.page.evaluate(
            """names => Object.fromEntries(
                names
                    .filter(name => typeof GLPIImpact[name] !== 'undefined')
                    .map(name => [name, GLPIImpact[name]])
            )""",
            names,
        )

    def current_state(self) -> dict[str, Any]:
        """Return GLPIImpact.getCurrentState() from the live workspace."""
        self.wait_until_ready()
        return self.page.evaluate("() => GLPIImpact.getCurrentState()")

    def initial_state(self) -> dict[str, Any]:
        """Return a serializable copy of GLPIImpact.initialState."""
        self.wait_until_ready()
        return self.page.evaluate(
            "() => JSON.parse(JSON.stringify(GLPIImpact.initialState || {}))"
        )

    def compute_delta(self) -> dict[str, Any]:
        """Ask GLPI itself to compute the pending workspace delta."""
        self.wait_until_ready()
        return self.page.evaluate("() => GLPIImpact.computeDelta()")

    def nodes(self) -> list[dict[str, Any]]:
        self.wait_until_ready()
        return self.page.evaluate(
            "() => GLPIImpact.cy.nodes().map(node => node.data())"
        )

    def edges(self) -> list[dict[str, Any]]:
        self.wait_until_ready()
        return self.page.evaluate(
            "() => GLPIImpact.cy.edges().map(edge => edge.data())"
        )

    def add_node(
        self,
        node: ImpactNode,
        position: dict[str, float] | None = None,
    ) -> Any:
        """Call GLPIImpact.addNode using the signature observed in GLPI Cloud."""
        self.wait_until_ready()
        position = position or {"x": node.x or 0, "y": node.y or 0}
        return self.page.evaluate(
            """args => GLPIImpact.addNode(
                args.items_id,
                args.itemtype,
                args.position
            )""",
            {
                "items_id": node.items_id,
                "itemtype": node.itemtype,
                "position": position,
            },
        )

    def has_node(self, node: ImpactNode) -> bool:
        self.wait_until_ready()
        return bool(
            self.page.evaluate(
                "id => GLPIImpact.cy.getElementById(id).length > 0",
                node.id,
            )
        )

    def has_edge(self, edge: ImpactEdge) -> bool:
        self.wait_until_ready()
        return bool(
            self.page.evaluate(
                "id => GLPIImpact.cy.getElementById(id).length > 0",
                edge.id,
            )
        )

    def set_edition_mode(self, mode: int) -> Any:
        """Delegate edition-mode selection to GLPIImpact."""
        self.wait_until_ready()
        return self.page.evaluate("mode => GLPIImpact.setEditionMode(mode)", mode)

    def enter_edition_mode(self) -> Any:
        self.wait_until_ready()
        return self.page.evaluate("() => GLPIImpact.enterEditionMode()")
