"""Redacted network evidence for GLPI Impact persistence discovery."""

from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from playwright.sync_api import Page, Request

SENSITIVE_HEADERS = {"authorization", "cookie", "proxy-authorization", "set-cookie", "x-glpi-csrf-token", "x-csrf-token"}
SENSITIVE_FIELDS = {"_glpi_csrf_token", "csrf", "csrf_token", "password", "login_password", "token", "access_token", "refresh_token", "secret", "api_key", "apikey"}


@dataclass(frozen=True)
class CapturedRequest:
    method: str
    url: str
    resource_type: str
    headers: dict[str, str]
    post_data: str | None


class ImpactNetworkRecorder:
    """Capture a short request window with secrets redacted before storage."""

    def __init__(self, page: Page, *, impact_only: bool = True):
        self.page = page
        self.impact_only = impact_only
        self.requests: list[CapturedRequest] = []
        self._active = False

    @staticmethod
    def _sensitive(name: str) -> bool:
        normalized = name.lower().replace("-", "_")
        return normalized in SENSITIVE_FIELDS or "password" in normalized or "secret" in normalized or "token" in normalized

    @classmethod
    def redact_headers(cls, headers: dict[str, str]) -> dict[str, str]:
        return {k: "<redacted>" if k.lower() in SENSITIVE_HEADERS or cls._sensitive(k) else v for k, v in headers.items()}

    @classmethod
    def redact_url(cls, url: str) -> str:
        parts = urlsplit(url)
        query = urlencode([(k, "<redacted>" if cls._sensitive(k) else v) for k, v in parse_qsl(parts.query, keep_blank_values=True)])
        return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))

    @classmethod
    def _redact_value(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: "<redacted>" if cls._sensitive(str(k)) else cls._redact_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [cls._redact_value(v) for v in value]
        return value

    @classmethod
    def redact_post_data(cls, post_data: str | None) -> str | None:
        if not post_data:
            return post_data
        try:
            return json.dumps(cls._redact_value(json.loads(post_data)), ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            pass
        pairs = parse_qsl(post_data, keep_blank_values=True)
        if pairs:
            return urlencode([(k, "<redacted>" if cls._sensitive(k) else v) for k, v in pairs])
        return "<opaque body omitted>"

    def _on_request(self, request: Request) -> None:
        if request.resource_type not in {"xhr", "fetch"}:
            return
        if self.impact_only and "impact" not in request.url.lower():
            return
        self.requests.append(CapturedRequest(
            method=request.method,
            url=self.redact_url(request.url),
            resource_type=request.resource_type,
            headers=self.redact_headers(request.headers),
            post_data=self.redact_post_data(request.post_data),
        ))

    def start(self) -> "ImpactNetworkRecorder":
        if not self._active:
            self.page.on("request", self._on_request)
            self._active = True
        return self

    def stop(self) -> list[CapturedRequest]:
        if self._active:
            self.page.remove_listener("request", self._on_request)
            self._active = False
        return list(self.requests)

    def clear(self) -> None:
        self.requests.clear()

    def snapshot(self) -> list[dict[str, Any]]:
        return [asdict(request) for request in self.requests]

    def export_json(self, path: str | Path) -> Path:
        destination = Path(path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(self.snapshot(), ensure_ascii=False, indent=2), encoding="utf-8")
        return destination
