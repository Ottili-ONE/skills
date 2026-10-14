#!/usr/bin/env python3
"""Shared helpers for the business-de skill scripts.

The only thing this module owns is ``load_config``: every script reads its
pinned versions from ``config/versions.json`` and never hardcodes a version.
"""
from __future__ import annotations

import json
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    """Walk up until we find the repo root (has business-de/config/versions.json)."""
    for cand in [start, *start.parents]:
        if (cand / "business-de" / "config" / "versions.json").exists():
            return cand
    return start


def load_config(path: str | Path = "config/versions.json") -> dict:
    """Load the pinned-versions config, resolving relative to the repo root.

    The config lives at ``<root>/business-de/config/versions.json``; the
    default argument is the path *inside* business-de so that scripts can
    pass it through unchanged.
    """
    p = Path(path)
    if not p.is_absolute():
        root = find_repo_root(Path(__file__).resolve().parent)
        p = root / "business-de" / p
    if not p.exists():
        raise FileNotFoundError(f"config not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))
