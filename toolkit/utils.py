from __future__ import annotations
from pathlib import Path
from typing import List, Optional

def ensure_dir(path: Path) -> Path:
    """Create directory if missing. Raises on permission errors."""
    path.mkdir(parents=True, exist_ok=True)
    return path

def parse_csv_list(s: Optional[str]) -> List[str]:
    if not s:
        return []
    out: List[str] = []
    for part in s.split(","):
        p = part.strip()
        if p:
            out.append(p)
    return out

def safe_str(v) -> str:
    return "N/A" if v is None else str(v)

def validate_file(path_str: str) -> Path:
    p = Path(path_str).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    if not p.is_file():
        raise IsADirectoryError(f"Path is not a file: {p}")
    return p
