"""Canonical clean-tree check for the skills repository (SKL-W0-01 TASK-0003).

The invariant: a checkout of this repository must leave ``git status --porcelain``
empty -- no modified files, no untracked leftovers. A test that writes into the
worktree (or into a fixed path outside it) must break the suite instead of
silently dirtying the tree.

One implementation, three entry points:

  * ``tests/hygiene/test_clean_tree.py``  -- the pytest guard, runs last
  * ``tests/conftest.py``                  -- the check after every test module
  * ``python3 tests/hygiene/clean_tree.py`` -- the command line
"""
from __future__ import annotations

import argparse
import subprocess
from collections.abc import Iterable
from pathlib import Path

SEED_NAME = ".hygiene-seed"


def repo_root() -> Path:
    """The root of the repository this file lives in."""
    return Path(__file__).resolve().parents[2]


def git_status_porcelain(root: Path) -> str:
    """The raw ``git status --porcelain`` output for *root*."""
    result = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git status failed in {root}: {result.stderr.strip()}")
    return result.stdout


def dirty_paths(root: Path) -> list[str]:
    """The paths that make the tree dirty; an empty list means clean."""
    return [line for line in git_status_porcelain(root).splitlines() if line.strip()]


def is_clean(root: Path) -> bool:
    """True when ``git status --porcelain`` reports nothing."""
    return not dirty_paths(root)


def dirt_added_since(baseline: Iterable[str], current: Iterable[str]) -> list[str]:
    """The paths that are dirty now but were not dirty when the session began."""
    return sorted(set(current) - set(baseline))


def seed_dirty(root: Path) -> Path:
    """Write a stray file into *root* so the checker has something to find."""
    seed = root / SEED_NAME
    seed.write_text("seeded by clean_tree.py\n", encoding="utf-8")
    return seed


def main(argv: list[str] | None = None) -> int:
    """Check the tree; with ``--dirty`` seed a stray file first."""
    parser = argparse.ArgumentParser(
        description="Check that the working tree has no uncommitted changes.",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="repository root to inspect (default: the repository this file is in)",
    )
    parser.add_argument(
        "--dirty",
        "--seed-dirty",
        dest="dirty",
        action="store_true",
        help="seed a stray file before checking (the negative case)",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else repo_root()

    seed = seed_dirty(root) if args.dirty else None
    try:
        dirty = dirty_paths(root)
    finally:
        if seed is not None:
            seed.unlink(missing_ok=True)

    if dirty:
        print(f"DIRTY: {len(dirty)} path(s) are not committed:")
        for line in dirty:
            print(f"  {line}")
        return 1
    print("CLEAN: git status --porcelain is empty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
