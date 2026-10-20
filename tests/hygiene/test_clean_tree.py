"""The clean-tree hygiene guard (SKL-W0-01 TASK-0003).

This module runs *after* every other test module (see ``tests/conftest.py``), so
a test that writes into the working tree fails the suite instead of quietly
dirtying it. The checker is proven against a deliberately dirty fixture in a
throwaway repository, so the guard cannot rot into a rubber stamp.

On a clean checkout (a fresh clone, CI) the session starts with an empty tree
and must end with an empty tree. On a checkout with pending work (a gate run, a
local patch) the session must at least not add anything to it.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from hygiene.clean_tree import (
    SEED_NAME,
    dirt_added_since,
    dirty_paths,
    is_clean,
    repo_root,
    seed_dirty,
)


pytestmark = pytest.mark.runs_last

GUARD_TEST_ID = (
    "tests/hygiene/test_clean_tree.py::test_worktree_is_clean_after_every_test_module"
)

_SEED_PLUGIN = r'''
"""pytest plugin that dirties the checkout during the session (the negative case)."""
import os
from pathlib import Path


def pytest_sessionstart(session):
    Path(os.environ["SKL_HYGIENE_SEED_FILE"]).write_text("seeded\n", encoding="utf-8")


def _remove():
    try:
        os.unlink(os.environ["SKL_HYGIENE_SEED_FILE"])
    except OSError:
        pass


def pytest_sessionfinish(session, exitstatus):
    _remove()


def pytest_unconfigure(config):
    _remove()
'''


def make_fixture_repo(root: Path) -> Path:
    """Create a throwaway git repository with one committed file."""
    root.mkdir(parents=True, exist_ok=True)

    def git(*args: str) -> None:
        subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    git("init", "-q")
    git("config", "user.email", "hygiene@example.invalid")
    git("config", "user.name", "Hygiene Fixture")
    (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    git("add", "tracked.txt")
    git("commit", "-q", "-m", "initial")
    return root


def test_checker_reports_a_clean_fixture(tmp_path: Path) -> None:
    """A repository without changes is clean."""
    root = make_fixture_repo(tmp_path / "clean")
    assert dirty_paths(root) == []
    assert is_clean(root) is True


def test_guard_fails_on_a_seeded_dirty_fixture(tmp_path: Path) -> None:
    """A deliberately seeded file is reported: the guard is not a rubber stamp."""
    root = make_fixture_repo(tmp_path / "dirty")
    baseline = dirty_paths(root)
    seed = seed_dirty(root)
    try:
        current = dirty_paths(root)
    finally:
        seed.unlink(missing_ok=True)
    added = dirt_added_since(baseline, current)
    assert added, "the guard would not notice the seeded file"
    assert any(SEED_NAME in line for line in added), added
    assert is_clean(root) is True, "the fixture must be clean again"


def test_worktree_is_clean_after_every_test_module(
    tree_baseline: frozenset[str],
) -> None:
    """The guard itself: the tests must not change the state of the tree."""
    current = dirty_paths(repo_root())
    added = dirt_added_since(tree_baseline, current)
    assert not added, (
        "the test suite dirtied the working tree:\n" + "\n".join(added)
    )
    if not tree_baseline:
        assert not current, (
            "the test suite dirtied the working tree:\n" + "\n".join(current)
        )


def test_the_guard_fails_when_a_test_dirties_the_worktree(tmp_path: Path) -> None:
    """End to end: a test that dirties the checkout must turn the suite red.

    The dirt is written by a plugin that runs inside a second pytest session, so
    the real guard runs against a really dirty tree. The second session must
    fail, the failure must name the stray file, and the repository must be free
    of it again afterwards.
    """
    root = repo_root()
    baseline = dirty_paths(root)
    seed = root / "pytest-seeded-dirt-{}.txt".format(os.getpid())
    (tmp_path / "seed_dirt_plugin.py").write_text(_SEED_PLUGIN, encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(tmp_path), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    env["SKL_HYGIENE_SEED_FILE"] = str(seed)

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "-p",
                "seed_dirt_plugin",
                "--confcutdir={}".format(root),
                "--rootdir={}".format(root),
                GUARD_TEST_ID,
                "-q",
            ],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
    finally:
        seed.unlink(missing_ok=True)

    output = result.stdout + result.stderr
    assert result.returncode != 0, (
        "the guard did not notice the dirtied tree:\n" + output
    )
    assert "dirtied the working tree" in output, output
    assert "the test module" in output, output
    assert seed.name in output, output
    added = dirt_added_since(baseline, dirty_paths(root))
    assert not added, "the seeded file was left behind:\n" + "\n".join(added)
