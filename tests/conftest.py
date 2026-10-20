"""Repository-level pytest configuration (SKL-W0-01 TASK-0003).

Three jobs:

1. Run the clean-tree hygiene guard *after* every other test module, so a test
   that writes into the working tree fails the suite instead of silently
   dirtying it.
2. Record the tree state at the start of the session. The guard compares the
   state at the end of the session with it: on a clean checkout the tree must
   still be clean, and on a checkout with pending work (a gate run, a local
   patch) the tests must not add anything to it.
3. Keep collection deterministic. The stale top-level ``business-de/`` duplicate
   was deleted in commit 0d5f964. The collection guard that excluded it also
   excluded the canonical ``skills/business-de/`` tests (218 of them) from every
   full run, so a third of the suite was never executed. That guard is gone;
   the invariant it tried to protect is enforced by a test now:
   ``tests/hygiene/test_skill_tree.py``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from hygiene.clean_tree import dirty_paths, repo_root

_TREE_BASELINE: frozenset[str] = frozenset()


def pytest_configure(config) -> None:
    """Register the hygiene marker and record the tree state of this session."""
    config.addinivalue_line(
        "markers", "runs_last: run this test after every other test module"
    )
    global _TREE_BASELINE
    _TREE_BASELINE = frozenset(dirty_paths(repo_root()))


def pytest_collection_modifyitems(config, items) -> None:
    """Move the ``runs_last`` tests to the end of the session.

    ``list.sort`` is stable, so the marked tests keep their relative order and
    every other test keeps the order pytest collected it in.
    """
    items.sort(key=lambda item: item.get_closest_marker("runs_last") is not None)


@pytest.fixture(scope="session")
def tree_baseline() -> frozenset[str]:
    """The dirty paths the session started with; empty on a clean checkout."""
    return _TREE_BASELINE
