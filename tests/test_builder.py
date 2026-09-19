"""Unit tests for GLPI edge delta recognition."""

from glpiimpact.impact.builder import ImpactBuilder
from glpiimpact.impact.graph import ImpactEdge, ImpactNode

EDGE = ImpactEdge(ImpactNode("Computer", 15), ImpactNode("Computer", 16))


def test_delta_detects_edge_key():
    assert ImpactBuilder.delta_mentions_edge({"edges": {EDGE.id: {"action": 1}}}, EDGE)


def test_delta_detects_observed_glpi_fields():
    delta = {"edges": {"x": {
        "itemtype_source": "Computer", "items_id_source": "15",
        "itemtype_impacted": "Computer", "items_id_impacted": "16",
    }}}
    assert ImpactBuilder.delta_mentions_edge(delta, EDGE)


def test_delta_rejects_unrelated_change():
    assert not ImpactBuilder.delta_mentions_edge(
        {"items": {"Computer::15": {"action": 2}}}, EDGE
    )
