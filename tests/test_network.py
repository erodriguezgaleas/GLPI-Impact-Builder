"""Unit tests for network redaction and response evidence helpers."""

import json
from glpiimpact.impact.network import CapturedRequest, ImpactNetworkRecorder


def test_redacts_sensitive_headers():
    result = ImpactNetworkRecorder.redact_headers({"cookie": "secret", "x-glpi-csrf-token": "csrf", "content-type": "application/json"})
    assert result["cookie"] == "<redacted>"
    assert result["x-glpi-csrf-token"] == "<redacted>"
    assert result["content-type"] == "application/json"


def test_redacts_url_query_tokens():
    result = ImpactNetworkRecorder.redact_url("https://example.test/ajax/impact.php?_glpi_csrf_token=secret&item=15")
    assert "secret" not in result
    assert "item=15" in result


def test_redacts_json_body_recursively():
    body = json.dumps({"edges": {}, "_glpi_csrf_token": "secret", "nested": {"access_token": "abc", "value": 7}})
    result = json.loads(ImpactNetworkRecorder.redact_post_data(body))
    assert result["_glpi_csrf_token"] == "<redacted>"
    assert result["nested"]["access_token"] == "<redacted>"
    assert result["nested"]["value"] == 7


def test_redacts_urlencoded_body():
    result = ImpactNetworkRecorder.redact_post_data("_glpi_csrf_token=secret&action=save")
    assert "secret" not in result
    assert "action=save" in result


def test_opaque_body_is_not_exposed():
    assert ImpactNetworkRecorder.redact_post_data("raw secret-ish payload without form encoding") == "<opaque body omitted>"


def test_bare_text_with_ampersand_is_still_opaque():
    assert ImpactNetworkRecorder.redact_post_data("one&two&three") == "<opaque body omitted>"


def test_successful_write_responses_excludes_reads_and_failures():
    recorder = object.__new__(ImpactNetworkRecorder)
    recorder.requests = [
        CapturedRequest("GET", "https://example.test/a", "xhr", {}, None, 200, True),
        CapturedRequest("POST", "https://example.test/b", "fetch", {}, "x=1", 200, True),
        CapturedRequest("POST", "https://example.test/c", "xhr", {}, "x=1", 500, False),
    ]
    result = recorder.successful_write_responses()
    assert len(result) == 1
    assert result[0]["url"] == "https://example.test/b"
    assert result[0]["status"] == 200
