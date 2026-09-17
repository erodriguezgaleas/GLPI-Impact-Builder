"""Safe network recorder for discovering GLPI Impact persistence requests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, Request

SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "proxy-authorization",
    "set-cookie",
    "x-glpi-csrf-token",
    "x-csrf-token",
}


@dataclass(frozen=True)
class CapturedRequest:
    method: str
    url: str
    resource_type: str
    headers: dict[str, str]
    post_data: str | None


class ImpactNetworkRecorder:
    """Capture Impact-related browser requests while redacting credentials."""

    def __init__(self, page: Page):
        self.page = page
        self.requests: list[CapturedRequest] = []
        self._active = False

    @staticmethod
    def redact_headers(headers: dict[str, str]) -> dict[str, str]:
        return {
            key: "<redacted>" if key.lower() in SENSITIVE_HEADERS else value
            for key, value in headers.items()
        }

    def _on_request(self, request: Request) -> None:
        url = request.url
        post_data = request.post_data
        if "impact" not in url.lower() and "impact" not in (post_data or "").lower():
            return
        self.requests.append(
            CapturedRequest(
                method=request.method,
                url=url,
                resource_type=request.resource_type,
                headers=self.redact_headers(request.headers),
                post_data=post_data,
            )
        )

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
        destination.write_text(
            json.dumps(self.snapshot(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return destination
