"""Unit tests for the GLPI Impact domain model."""

from glpiimpact.impact.graph import ImpactEdge, ImpactGraph, ImpactNode


def test_node_id_uses_glpi_separator():
    node = ImpactNode("Computer", 15)
    assert node.id == "Computer::15"


def test_edge_id_uses_glpi_separator():
    source = ImpactNode("Computer", 15)
    target = ImpactNode("Computer", 16)
    edge = ImpactEdge(source, target)
    assert edge.id == "Computer::15->Computer::16"


def test_edge_delta_matches_observed_glpi_shape():
    edge = ImpactEdge(ImpactNode("Computer", 15), ImpactNode("Computer", 16))
    assert edge.as_glpi_delta() == {
        "action": 1,
        "itemtype_source": "Computer",
        "items_id_source": "15",
        "itemtype_impacted": "Computer",
        "items_id_impacted": "16",
    }


def test_graph_add_edge_registers_nodes_and_edge():
    graph = ImpactGraph()
    source = ImpactNode("Computer", 15)
    target = ImpactNode("Computer", 16)
    edge = graph.add_edge(source, target)

    assert graph.nodes == {source.id: source, target.id: target}
    assert graph.edges == {edge.id: edge}
    assert graph.edge_delta() == {edge.id: edge.as_glpi_delta()}
