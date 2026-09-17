"""Domain model for GLPI Impact nodes and directed relationships."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

NODE_ID_SEPARATOR = "::"
EDGE_ID_SEPARATOR = "->"


@dataclass(frozen=True)
class ImpactNode:
    itemtype: str
    items_id: int
    label: str | None = None
    impactitem_id: int | None = None
    x: float | None = None
    y: float | None = None

    @property
    def id(self) -> str:
        return f"{self.itemtype}{NODE_ID_SEPARATOR}{self.items_id}"


@dataclass(frozen=True)
class ImpactEdge:
    source: ImpactNode
    impacted: ImpactNode

    @property
    def id(self) -> str:
        return f"{self.source.id}{EDGE_ID_SEPARATOR}{self.impacted.id}"

    def as_glpi_delta(self, action: int = 1) -> dict[str, Any]:
        """Return the edge shape observed in GLPI Impact delta payloads."""
        return {
            "action": action,
            "itemtype_source": self.source.itemtype,
            "items_id_source": str(self.source.items_id),
            "itemtype_impacted": self.impacted.itemtype,
            "items_id_impacted": str(self.impacted.items_id),
        }


@dataclass
class ImpactGraph:
    nodes: dict[str, ImpactNode] = field(default_factory=dict)
    edges: dict[str, ImpactEdge] = field(default_factory=dict)

    def add_node(self, node: ImpactNode) -> ImpactNode:
        self.nodes[node.id] = node
        return node

    def add_edge(self, source: ImpactNode, impacted: ImpactNode) -> ImpactEdge:
        self.add_node(source)
        self.add_node(impacted)
        edge = ImpactEdge(source=source, impacted=impacted)
        self.edges[edge.id] = edge
        return edge

    def edge_delta(self, action: int = 1) -> dict[str, dict[str, Any]]:
        return {edge_id: edge.as_glpi_delta(action) for edge_id, edge in self.edges.items()}
