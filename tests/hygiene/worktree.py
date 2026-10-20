"""A throwaway checkout of this repository, for tests that need a second tree.

A test that adds a file to the checkout it runs in would dirty the repository it
tests. A **linked worktree** gives the test a second tree of the same repository
without touching the first one, and the commands of the shape document
(``git ls-files | wc -l``) run inside it unchanged.

The worktree is removed again in the ``finally`` branch, and the metadata that
``git worktree add`` leaves in ``.git/worktrees`` is pruned, so the repository
that runs the test is left exactly as it was.
"""
from __future__ import annotations

import contextlib
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@contextlib.contextmanager
def temporary_worktree(revision: str = "HEAD") -> Iterator[Path]:
    """Yield a throwaway checkout of a revision of this repository."""
    holder = Path(tempfile.mkdtemp(prefix="repo-worktree-"))
    target = holder / "tree"
    subprocess.run(
        ["git", "worktree", "add", "--detach", "--quiet", str(target), revision],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        yield target
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(target)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        shutil.rmtree(holder, ignore_errors=True)
