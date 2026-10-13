"""Shared helpers for the business-de skills scripts.

Resolves the pinned versions config relative to the repo root so every script
can be run from any working directory. Never hardcode a version.
"""
import json
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    """Walk up until we find the repo root (has business-de/config/versions.json)."""
    for cand in [start, *start.parents]:
        if (cand / "business-de" / "config" / "versions.json").exists():
            return cand
    return start


def load_config(path: str = "config/versions.json") -> dict:
    """Load the pinned versions config.

    Resolution order, so a script works from any CWD:
      1. an absolute path that exists;
      2. the path as given, relative to CWD;
      3. the same relative path under the repo root (``business-de/<path>``);
      4. the same relative path under the calling script's own skill dir
         (``<skill>/config/versions.json``) — this is the common case when a
         skill's script is invoked with its own default ``--config`` value.
    Never hardcode a version; every script reads it from here.
    """
    p = Path(path)
    if p.is_absolute() and p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    root = find_repo_root(Path(__file__).resolve().parent)
    alt = root / "business-de" / path
    if alt.exists():
        return json.loads(alt.read_text(encoding="utf-8"))
    # fall back to the caller's own skill dir: <scripts>/../config/<path>
    caller = Path(sys._getframe(1).f_code.co_filename).resolve().parent
    for cand in (caller / "config" / Path(path).name,
                 caller.parent / "config" / Path(path).name):
        if cand.exists():
            return json.loads(cand.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"versions config not found for {path!r}")


def sha256_of(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
