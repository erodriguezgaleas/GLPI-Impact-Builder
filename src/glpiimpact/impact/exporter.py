"""Export live GLPI Impact workspaces to portable JSON documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .builder import ImpactBuilder


class ImpactExporter:
    def __init__(self, builder: ImpactBuilder):
        self.builder = builder

    def snapshot(self, include_delta: bool = True) -> dict[str, Any]:
        """Capture graph elements and GLPI workspace state."""
        document: dict[str, Any] = {
            "format": "glpi-impact-builder/v1",
            "nodes": self.builder.nodes(),
            "edges": self.builder.edges(),
            "current_state": self.builder.current_state(),
            "initial_state": self.builder.initial_state(),
        }
        if include_delta:
            document["delta"] = self.builder.compute_delta()
        return document

    def export_json(
        self,
        path: str | Path,
        *,
        include_delta: bool = True,
        indent: int = 2,
    ) -> Path:
        destination = Path(path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(
                self.snapshot(include_delta=include_delta),
                ensure_ascii=False,
                indent=indent,
            ),
            encoding="utf-8",
        )
        return destination
