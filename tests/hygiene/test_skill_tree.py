"""The skill tree must have exactly one home for every skill package.

The stale top-level ``business-de/`` duplicate was deleted in commit 0d5f964.
The collection guard that excluded it also excluded the canonical
``skills/business-de/`` tests from every full run, so 218 passing tests were
never executed. The guard is gone; this test keeps the invariant honest
instead of hiding tests.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
SKIPPED_DIR_NAMES = {
    ".git",
    ".germo",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".truth",
    "__pycache__",
    "node_modules",
}


def skill_packages() -> list[str]:
    """The package names that live under skills/."""
    return sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())


def stray_directories() -> list[str]:
    """Directories outside skills/ that carry a skill package name."""
    packages = set(skill_packages())
    strays: list[str] = []
    for dirpath, dirnames, _files in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIPPED_DIR_NAMES]
        here = Path(dirpath)
        if here == SKILLS_DIR:
            dirnames[:] = []
            continue
        if SKILLS_DIR in here.parents:
            continue
        if here.name in packages:
            strays.append(str(here.relative_to(REPO_ROOT)))
    return sorted(strays)


def test_no_duplicate_skill_directory() -> None:
    """Every skill package exists exactly once, and only under skills/."""
    strays = stray_directories()
    assert not strays, (
        "skill packages must live under skills/ only; copies found at: "
        + ", ".join(strays)
    )
