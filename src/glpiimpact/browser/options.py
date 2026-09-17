"""Browser configuration options."""

from dataclasses import dataclass
from pathlib import Path

@dataclass(slots=True)
class BrowserOptions:
    headless: bool = False
    slow_mo: int = 0
    timeout: int = 60000
    viewport_width: int = 1600
    viewport_height: int = 900
    accept_downloads: bool = True
    download_path: Path = Path("downloads")
