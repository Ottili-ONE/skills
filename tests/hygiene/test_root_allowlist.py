"""Invariant: the repository root holds nothing but the allow-listed entries
(SKL-W0-01, TASK-0006).

``rootAllowlist`` in ``scripts/truth/config.json`` is the single source of
truth for what may live at the root of the repository. A scratch directory, a
debug probe or a stray artefact at the root is rejected; the check reads the
allow-list from the config of the repository it judges, so a fixture is judged
by its own rules.
"""
from __future__ import annotations

from pathlib import Path

from hygiene.repo_guard import (
    REPO_ROOT,
    FixtureFile,
    make_repo,
    root_allowlist,
    root_violations,
    stale_allowlist_entries,
)

# "scripts" hosts the config of the fixture itself, so the fixture allows it.
FIXTURE_CONFIG = {"rootAllowlist": ["README.md", "docs", "scripts"]}


def test_every_tracked_root_entry_is_allow_listed() -> None:
    """The real repository root matches the allow-list of its config."""
    violations = root_violations(REPO_ROOT)
    assert violations == [], (
        f"entries at the repository root that the allow-list does not cover: {violations}"
    )


def test_the_root_allowlist_has_no_stale_entry() -> None:
    """Every allow-listed root entry still exists in the checkout."""
    stale = stale_allowlist_entries(REPO_ROOT)
    assert stale == [], f"the allow-list mentions entries that do not exist: {stale}"


def test_the_allow_list_is_read_from_the_config_of_the_repository(tmp_path: Path) -> None:
    """The allow-list comes from the config, not from a hard-coded list."""
    repo = make_repo(
        tmp_path,
        [FixtureFile(path="README.md", content="fixture")],
        config=FIXTURE_CONFIG,
    )
    assert root_allowlist(repo) == ["README.md", "docs", "scripts"]
    assert root_violations(repo) == []


def test_detects_a_scratch_directory_in_a_fixture(tmp_path: Path) -> None:
    """A scratch directory at the root of a fixture is reported."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(path="README.md", content="fixture"),
            FixtureFile(path="scratch/probe.py", content="raise SystemExit(1)\n"),
        ],
        config=FIXTURE_CONFIG,
    )
    assert root_violations(repo) == ["scratch"]


def test_detects_a_debug_script_in_a_fixture(tmp_path: Path) -> None:
    """A debug script at the root of a fixture is reported."""
    repo = make_repo(
        tmp_path,
        [
            FixtureFile(path="README.md", content="fixture"),
            FixtureFile(path="_dbg-probe.py", content="print('probe')\n"),
        ],
        config=FIXTURE_CONFIG,
    )
    assert root_violations(repo) == ["_dbg-probe.py"]


def test_detects_a_stale_allow_list_entry_in_a_fixture(tmp_path: Path) -> None:
    """An allow-list entry without a counterpart in the checkout is reported."""
    repo = make_repo(
        tmp_path,
        [FixtureFile(path="README.md", content="fixture")],
        config=FIXTURE_CONFIG,
    )
    assert stale_allowlist_entries(repo) == ["docs"]
