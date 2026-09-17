"""Read portable GLPI Impact Builder JSON snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ImpactImporter:
    """Validate and read snapshots produced by :class:`ImpactExporter`.

    Importing a file does not mutate GLPI automatically. Applying nodes and
    relationships is intentionally kept separate so mutations remain explicit.
    """

    FORMAT = "glpi-impact-builder/v1"

    def load_json(self, path: str | Path) -> dict[str, Any]:
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Impact snapshot not found: {source}")

        document = json.loads(source.read_text(encoding="utf-8"))
        return self.validate(document)

    def validate(self, document: Any) -> dict[str, Any]:
        if not isinstance(document, dict):
            raise ValueError("Impact snapshot must be a JSON object")
        if document.get("format") != self.FORMAT:
            raise ValueError(
                f"Unsupported impact snapshot format: {document.get('format')!r}"
            )
        if not isinstance(document.get("nodes"), list):
            raise ValueError("Impact snapshot must contain a nodes list")
        if not isinstance(document.get("edges"), list):
            raise ValueError("Impact snapshot must contain an edges list")
        return document
