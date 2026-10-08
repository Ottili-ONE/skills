"""Shared helpers for the business-de skills scripts.

Resolves the pinned versions config relative to the repo root so every script
can be run from any working directory. Never hardcode a version.
"""
import json
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    """Walk up until we find the repo root (has business-de/config/versions.json)."""
    for cand in [start, *start.parents]:
        if (cand / "business-de" / "config" / "versions.json").exists():
            return cand
    return start


def load_config(path: str = "config/versions.json") -> dict:
    """Load the pinned versions config, resolving relative to the repo root."""
    p = Path(path)
    if not p.is_absolute() and not p.exists():
        root = find_repo_root(Path(__file__).resolve().parent)
        alt = root / "business-de" / path
        if alt.exists():
            p = alt
    return json.loads(p.read_text(encoding="utf-8"))


def sha256_of(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
