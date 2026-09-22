"""Redacted network evidence for GLPI Impact persistence discovery."""

from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from playwright.sync_api import Page, Request, Response

SENSITIVE_HEADERS = {"authorization", "cookie", "proxy-authorization", "set-cookie", "x-glpi-csrf-token", "x-csrf-token"}
SENSITIVE_FIELDS = {"_glpi_csrf_token", "csrf", "csrf_token", "password", "login_password", "token", "access_token", "refresh_token", "secret", "api_key", "apikey"}


@dataclass
class CapturedRequest:
    method: str
    url: str
    resource_type: str
    headers: dict[str, str]
    post_data: str | None
    status: int | None = None
    ok: bool | None = None


class ImpactNetworkRecorder:
    """Capture a short XHR/fetch window with secrets redacted before storage."""

    def __init__(self, page: Page, *, impact_only: bool = True):
        self.page = page
        self.impact_only = impact_only
        self.requests: list[CapturedRequest] = []
        self._active = False
        self._pending: dict[int, CapturedRequest] = {}

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
        # parse_qsl treats any bare text as a key with an empty value. Only
        # classify the body as form-encoded when assignment syntax is present.
        pairs = parse_qsl(post_data, keep_blank_values=True) if "=" in post_data else []
        if pairs:
            return urlencode([(k, "<redacted>" if cls._sensitive(k) else v) for k, v in pairs])
        return "<opaque body omitted>"

    def _accept(self, request: Request) -> bool:
        return request.resource_type in {"xhr", "fetch"} and (
            not self.impact_only or "impact" in request.url.lower()
        )

    def _on_request(self, request: Request) -> None:
        if not self._accept(request):
            return
        captured = CapturedRequest(
            method=request.method,
            url=self.redact_url(request.url),
            resource_type=request.resource_type,
            headers=self.redact_headers(request.headers),
            post_data=self.redact_post_data(request.post_data),
        )
        self.requests.append(captured)
        self._pending[id(request)] = captured

    def _on_response(self, response: Response) -> None:
        captured = self._pending.pop(id(response.request), None)
        if captured is None:
            return
        captured.status = response.status
        captured.ok = response.ok

    def start(self) -> "ImpactNetworkRecorder":
        if not self._active:
            self.page.on("request", self._on_request)
            self.page.on("response", self._on_response)
            self._active = True
        return self

    def stop(self) -> list[CapturedRequest]:
        if self._active:
            self.page.remove_listener("request", self._on_request)
            self.page.remove_listener("response", self._on_response)
            self._active = False
        self._pending.clear()
        return list(self.requests)

    def clear(self) -> None:
        self.requests.clear()
        self._pending.clear()

    def snapshot(self) -> list[dict[str, Any]]:
        return [asdict(request) for request in self.requests]

    def successful_write_responses(self) -> list[dict[str, Any]]:
        return [
            item for item in self.snapshot()
            if item["method"].upper() not in {"GET", "HEAD", "OPTIONS"}
            and item["ok"] is True
        ]

    def export_json(self, path: str | Path) -> Path:
        destination = Path(path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(self.snapshot(), ensure_ascii=False, indent=2), encoding="utf-8")
        return destination
