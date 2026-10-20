"""Invariant: no tracked database or journal file (SKL-W0-01, TASK-0006).

``*.db``, ``*.db-wal``, ``*.db-shm``, ``*.sqlite*`` and ``*.journal*`` are
runtime state of a local database. Tracked, they drag the state of the machine
that created them into every clone and make the tree unreproducible.

The invariant is proven against the real repository and against a fixture that
carries one artefact of each kind.
"""
from __future__ import annotations

from pathlib import Path

from hygiene.repo_guard import REPO_ROOT, FixtureFile, database_violations, make_repo


def test_no_database_or_journal_file_is_tracked() -> None:
    """The real repository tracks no database or journal artefact."""
    violations = database_violations(REPO_ROOT)
    assert violations == [], f"database artefacts are tracked: {violations}"


def test_detects_a_db_file_in_a_fixture(tmp_path: Path) -> None:
    """A tracked ``*.db`` file is reported."""
    repo = make_repo(
        tmp_path,
        [FixtureFile(path="state.db", content="SQLite format 3\\0")],
    )
    assert database_violations(repo) == ["state.db"]


def test_detects_a_wal_file_in_a_fixture(tmp_path: Path) -> None:
    """A tracked ``*.db-wal`` file is reported."""
    repo = make_repo(tmp_path, [FixtureFile(path="state.db-wal", content="wal")])
    assert database_violations(repo) == ["state.db-wal"]


def test_detects_a_shm_file_in_a_fixture(tmp_path: Path) -> None:
    """A tracked ``*.db-shm`` file is reported."""
    repo = make_repo(tmp_path, [FixtureFile(path="state.db-shm", content="shm")])
    assert database_violations(repo) == ["state.db-shm"]


def test_detects_a_sqlite_file_in_a_fixture(tmp_path: Path) -> None:
    """A tracked ``*.sqlite`` file is reported."""
    repo = make_repo(tmp_path, [FixtureFile(path="cache.sqlite", content="db")])
    assert database_violations(repo) == ["cache.sqlite"]


def test_detects_a_journal_file_in_a_fixture(tmp_path: Path) -> None:
    """A tracked ``*.journal`` file is reported."""
    repo = make_repo(tmp_path, [FixtureFile(path="state.journal", content="j")])
    assert database_violations(repo) == ["state.journal"]


def test_accepts_a_file_that_merely_mentions_the_pattern(tmp_path: Path) -> None:
    """A tracked file whose name only resembles a database artefact is kept."""
    repo = make_repo(
        tmp_path,
        [FixtureFile(path="docs/database.md", content="no artefact here")],
    )
    assert database_violations(repo) == []
