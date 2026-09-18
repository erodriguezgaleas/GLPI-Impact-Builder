"""Safe network recorder for discovering GLPI Impact persistence requests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode

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
    """Capture Impact-related requests while redacting credentials and tokens."""

    def __init__(self, page: Page):
        self.page = page
        self.requests: list[CapturedRequest] = []
        self._active = False

    @staticmethod
    def _sensitive(name: str) -> bool:
        normalized = name.lower().replace("-", "_")
        return normalized in SENSITIVE_FIELDS or "password" in normalized or "secret" in normalized or "token" in normalized

    @classmethod
    def redact_headers(cls, headers: dict[str, str]) -> dict[str, str]:
        return {key: "<redacted>" if key.lower() in SENSITIVE_HEADERS or cls._sensitive(key) else value for key, value in headers.items()}

    @classmethod
    def _redact_value(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: "<redacted>" if cls._sensitive(str(key)) else cls._redact_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._redact_value(item) for item in value]
        return value

    @classmethod
    def redact_post_data(cls, post_data: str | None) -> str | None:
        if not post_data:
            return post_data
        try:
            parsed = json.loads(post_data)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if parsed is not None:
            return json.dumps(cls._redact_value(parsed), ensure_ascii=False)

        try:
            pairs = parse_qsl(post_data, keep_blank_values=True)
            if pairs:
                return urlencode([(key, "<redacted>" if cls._sensitive(key) else value) for key, value in pairs])
        except ValueError:
            pass

        lowered = post_data.lower()
        if any(field in lowered for field in SENSITIVE_FIELDS):
            return "<redacted: unstructured sensitive body>"
        return post_data

    def _on_request(self, request: Request) -> None:
        url = request.url
        raw_post_data = request.post_data
        if "impact" not in url.lower() and "impact" not in (raw_post_data or "").lower():
            return
        self.requests.append(CapturedRequest(method=request.method, url=url, resource_type=request.resource_type, headers=self.redact_headers(request.headers), post_data=self.redact_post_data(raw_post_data)))

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
