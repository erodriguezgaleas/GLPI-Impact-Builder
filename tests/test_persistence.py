"""Unit tests for guarded Impact persistence helpers."""

from glpiimpact.impact.persistence import ImpactPersistence, SaveResult


def test_empty_delta_has_no_changes():
    assert not ImpactPersistence._contains_change({})
    assert not ImpactPersistence._contains_change({"edges": {}, "items": []})


def test_nested_delta_detects_change():
    delta = {"edges": {"Computer::15->Computer::16": {"action": 1, "itemtype_source": "Computer"}}}
    assert ImpactPersistence._contains_change(delta)


def test_falsey_metadata_is_not_a_change():
    delta = {"edges": {}, "dirty": False, "count": 0, "message": ""}
    assert not ImpactPersistence._contains_change(delta)


def test_save_result_can_distinguish_reload_verification():
    result = SaveResult(
        attempted=True,
        persisted=True,
        dry_run=False,
        delta_before={"edges": {"x": {"action": 1}}},
        delta_after={},
        delta_cleared=True,
        verification="verified_after_reload",
        reloaded_edge_present=True,
    )
    assert result.persisted
    assert result.reloaded_edge_present is True
    assert result.verification == "verified_after_reload"
