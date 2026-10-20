"""Repository-level pytest configuration (SKL-W0-01 TASK-0003).

Four jobs:

1. Run the clean-tree hygiene guard *after* every other test module, so a test
   that writes into the working tree fails the suite instead of silently
   dirtying it.
2. Check the tree at the end of *every* test module, not only at the end of the
   session, so dirt is reported by the module that caused it.
3. Record the tree state at the start of the session. The guard compares the
   state at the end of the session with it: on a clean checkout the tree must
   still be clean, and on a checkout with pending work (a gate run, a local
   patch) the tests must not add anything to it.
4. Keep collection deterministic. The stale top-level ``business-de/`` duplicate
   was deleted in commit 0d5f964. The collection guard that excluded it also
   excluded the canonical ``skills/business-de/`` tests (218 of them) from every
   full run, so a third of the suite was never executed. That guard is gone;
   the invariant it tried to protect is enforced by a test now:
   ``tests/hygiene/test_skill_tree.py``.
"""
from __future__ import annotations

import pytest
from hygiene.clean_tree import dirt_added_since, dirty_paths, repo_root

_TREE_BASELINE: frozenset[str] = frozenset()


def pytest_configure(config: pytest.Config) -> None:
    """Register the hygiene marker and record the tree state of this session."""
    config.addinivalue_line(
        "markers", "runs_last: run this test after every other test module"
    )
    global _TREE_BASELINE
    _TREE_BASELINE = frozenset(dirty_paths(repo_root()))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Move the ``runs_last`` tests to the end of the session.

    ``list.sort`` is stable, so the marked tests keep their relative order and
    every other test keeps the order pytest collected it in.
    """
    items.sort(key=lambda item: item.get_closest_marker("runs_last") is not None)


def _module_of(item: pytest.Item) -> str:
    """The file a test item belongs to; the granularity of the module check."""
    return item.nodeid.split("::", 1)[0]


def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:
    """Check the tree after every test module has run.

    The check compares the tree with the state at the start of the session, so a
    checkout that already carries pending work is judged on what the tests
    added, not on what was there before. A module that leaves dirt behind is
    reported by the module it belongs to instead of by the end-of-session
    guard, which only sees the end state.
    """
    if nextitem is not None and _module_of(nextitem) == _module_of(item):
        return
    added = dirt_added_since(_TREE_BASELINE, dirty_paths(repo_root()))
    if added:
        pytest.fail(
            "the test module {} dirtied the working tree:\n{}".format(
                _module_of(item), "\n".join(added)
            ),
            pytrace=False,
        )


@pytest.fixture(scope="session")
def tree_baseline() -> frozenset[str]:
    """The dirty paths the session started with; empty on a clean checkout."""
    return _TREE_BASELINE
