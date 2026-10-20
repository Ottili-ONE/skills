"""Invariant: no tracked file above 5 MiB that is not allow-listed with a
reason (SKL-W0-01, TASK-0006).

Large blobs in version control bloat every clone and hide the real change of a
review. The allow-list lives in ``scripts/truth/config.json``
(``largeFileAllowlist``) and every entry has to carry a reason, so an
exception is a decision and not an accident.
"""
from __future__ import annotations

from pathlib import Path

from hygiene.repo_guard import (
    MAX_LARGE_FILE_BYTES,
    REPO_ROOT,
    FixtureFile,
    allowlist_without_reason,
    large_file_violations,
    make_repo,
)


def test_no_tracked_file_is_above_five_mebibytes() -> None:
    """The real repository tracks no file above the limit."""
    violations = large_file_violations(REPO_ROOT)
    assert violations == [], f"large files are tracked: {violations}"


def test_every_large_file_allow_list_entry_has_a_reason() -> None:
    """An allow-listed large file is justified in writing."""
    without_reason = allowlist_without_reason(REPO_ROOT)
    assert without_reason == [], (
        f"allow-listed large files without a reason: {without_reason}"
    )


def test_detects_a_large_file_in_a_fixture(tmp_path: Path) -> None:
    """A fixture that tracks a 6 MiB blob is reported."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(path="blob.bin", size=6 * 1024 * 1024),
            FixtureFile(
                path="scripts/truth/config.json",
                content='{"largeFileAllowlist": []}',
            ),
        ],
    )
    violations = large_file_violations(repo)
    assert violations == [f"blob.bin: {6 * 1024 * 1024} bytes"]


def test_accepts_an_allow_listed_large_file_in_a_fixture(tmp_path: Path) -> None:
    """A large file with an allow-list entry is accepted."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(path="blob.bin", size=6 * 1024 * 1024),
            FixtureFile(
                path="scripts/truth/config.json",
                content=(
                    '{"largeFileAllowlist": ['
                    '{"path": "blob.bin", "reason": "fixture"}]}'
                ),
            ),
        ],
    )
    assert large_file_violations(repo) == []
    assert allowlist_without_reason(repo) == []


def test_reports_an_allow_list_entry_without_a_reason(tmp_path: Path) -> None:
    """An allow-list entry without a reason is reported."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(
                path="scripts/truth/config.json",
                content='{"largeFileAllowlist": [{"path": "blob.bin"}]}',
            ),
        ],
    )
    assert allowlist_without_reason(repo) == ["blob.bin"]


def test_the_limit_is_five_mebibytes() -> None:
    """The documented limit is 5 MiB, not 5 MB."""
    assert MAX_LARGE_FILE_BYTES == 5 * 1024 * 1024
