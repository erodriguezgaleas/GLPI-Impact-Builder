"""Unit tests for guarded Impact persistence helpers."""

from glpiimpact.impact.persistence import ImpactPersistence


def test_empty_delta_has_no_changes():
    assert not ImpactPersistence._contains_change({})
    assert not ImpactPersistence._contains_change({"edges": {}, "items": []})


def test_nested_delta_detects_change():
    delta = {
        "edges": {
            "Computer::15->Computer::16": {
                "action": 1,
                "itemtype_source": "Computer",
            }
        }
    }
    assert ImpactPersistence._contains_change(delta)


def test_falsey_metadata_is_not_a_change():
    delta = {"edges": {}, "dirty": False, "count": 0, "message": ""}
    assert not ImpactPersistence._contains_change(delta)
