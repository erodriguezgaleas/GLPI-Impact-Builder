"""Application settings for GLPI Impact Builder."""

from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    url: str
    username: str
    password: str
    headless: bool = False
    timeout: int = 60000
    download_path: Path = Path("downloads")
