"""Unit tests for network redaction helpers."""

import json

from glpiimpact.impact.network import ImpactNetworkRecorder


def test_redacts_sensitive_headers():
    headers = {"cookie": "secret", "x-glpi-csrf-token": "csrf", "content-type": "application/json"}
    result = ImpactNetworkRecorder.redact_headers(headers)
    assert result["cookie"] == "<redacted>"
    assert result["x-glpi-csrf-token"] == "<redacted>"
    assert result["content-type"] == "application/json"


def test_redacts_json_body_recursively():
    body = json.dumps({"edges": {}, "_glpi_csrf_token": "secret", "nested": {"access_token": "abc", "value": 7}})
    result = json.loads(ImpactNetworkRecorder.redact_post_data(body))
    assert result["_glpi_csrf_token"] == "<redacted>"
    assert result["nested"]["access_token"] == "<redacted>"
    assert result["nested"]["value"] == 7


def test_redacts_urlencoded_body():
    result = ImpactNetworkRecorder.redact_post_data("_glpi_csrf_token=secret&action=save")
    assert "%3Credacted%3E" in result
    assert "secret" not in result
    assert "action=save" in result
