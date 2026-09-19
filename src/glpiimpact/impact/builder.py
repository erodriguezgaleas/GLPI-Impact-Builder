"""Browser-backed adapter for the GLPIImpact JavaScript workspace."""

from __future__ import annotations
from typing import Any
from playwright.sync_api import Page
from .graph import ImpactEdge, ImpactNode


class ImpactBuilder:
    """Interact with the GLPI Impact workspace through the browser page."""

    def __init__(self, page: Page):
        self.page = page

    def wait_until_ready(self, timeout: int = 30_000) -> None:
        self.page.wait_for_function("() => Boolean(window.GLPIImpact && GLPIImpact.cy)", timeout=timeout)

    def is_ready(self) -> bool:
        return bool(self.page.evaluate("() => Boolean(window.GLPIImpact && GLPIImpact.cy)"))

    def constants(self) -> dict[str, Any]:
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
        return self.page.evaluate("""names => Object.fromEntries(names
            .filter(name => typeof GLPIImpact[name] !== 'undefined')
            .map(name => [name, GLPIImpact[name]]))""", names)

    def methods(self) -> list[str]:
        self.wait_until_ready()
        return self.page.evaluate("""() => {
            const names = new Set(); let object = GLPIImpact;
            while (object && object !== Object.prototype) {
                Object.getOwnPropertyNames(object).forEach(name => names.add(name));
                object = Object.getPrototypeOf(object);
            }
            return [...names].filter(name => typeof GLPIImpact[name] === 'function').sort();
        }""")

    def current_state(self) -> dict[str, Any]:
        self.wait_until_ready()
        return self.page.evaluate("() => JSON.parse(JSON.stringify(GLPIImpact.getCurrentState()))")

    def initial_state(self) -> dict[str, Any]:
        self.wait_until_ready()
        return self.page.evaluate("() => JSON.parse(JSON.stringify(GLPIImpact.initialState || {}))")

    def compute_delta(self) -> dict[str, Any]:
        self.wait_until_ready()
        return self.page.evaluate("() => JSON.parse(JSON.stringify(GLPIImpact.computeDelta()))")

    def nodes(self) -> list[dict[str, Any]]:
        self.wait_until_ready()
        return self.page.evaluate("() => GLPIImpact.cy.nodes().map(n => JSON.parse(JSON.stringify(n.data())))")

    def edges(self) -> list[dict[str, Any]]:
        self.wait_until_ready()
        return self.page.evaluate("() => GLPIImpact.cy.edges().map(e => JSON.parse(JSON.stringify(e.data())))")

    def add_node(self, node: ImpactNode, position: dict[str, float] | None = None) -> Any:
        self.wait_until_ready()
        position = position or {"x": node.x or 0, "y": node.y or 0}
        return self.page.evaluate(
            "args => GLPIImpact.addNode(args.items_id, args.itemtype, args.position)",
            {"items_id": node.items_id, "itemtype": node.itemtype, "position": position},
        )

    def has_node(self, node: ImpactNode) -> bool:
        self.wait_until_ready()
        return bool(self.page.evaluate("id => GLPIImpact.cy.getElementById(id).length > 0", node.id))

    def has_edge(self, edge: ImpactEdge) -> bool:
        self.wait_until_ready()
        return bool(self.page.evaluate("id => GLPIImpact.cy.getElementById(id).length > 0", edge.id))

    @staticmethod
    def delta_mentions_edge(delta: dict[str, Any], edge: ImpactEdge) -> bool:
        source_id, target_id = str(edge.source.items_id), str(edge.impacted.items_id)
        def walk(value: Any) -> bool:
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

    def add_edge_to_workspace(self, edge: ImpactEdge) -> dict[str, Any]:
        """Experimental Cytoscape insertion; caller must verify GLPI delta."""
        self.wait_until_ready()
        if not self.has_node(edge.source) or not self.has_node(edge.impacted):
            raise ValueError("Both edge endpoints must already exist in the GLPI Impact workspace")
        if self.has_edge(edge):
            delta = self.compute_delta()
            return {"created": False, "edge_id": edge.id, "delta": delta, "delta_detected": self.delta_mentions_edge(delta, edge)}

        result = self.page.evaluate("""args => {
            const element = GLPIImpact.cy.add({
                group: 'edges',
                data: {id: args.id, source: args.source, target: args.target}
            });
            return {id: element.id(), data: JSON.parse(JSON.stringify(element.data()))};
        }""", {"id": edge.id, "source": edge.source.id, "target": edge.impacted.id})
        delta = self.compute_delta()
        return {"created": True, "edge": result, "delta": delta, "delta_detected": self.delta_mentions_edge(delta, edge)}

    def remove_workspace_element(self, element_id: str) -> bool:
        self.wait_until_ready()
        return bool(self.page.evaluate("""id => {
            const element = GLPIImpact.cy.getElementById(id);
            if (!element.length) return false;
            GLPIImpact.cy.remove(element); return true;
        }""", element_id))

    def set_edition_mode(self, mode: int) -> Any:
        self.wait_until_ready()
        return self.page.evaluate("mode => GLPIImpact.setEditionMode(mode)", mode)

    def enter_edition_mode(self) -> Any:
        self.wait_until_ready()
        return self.page.evaluate("() => GLPIImpact.enterEditionMode()")
