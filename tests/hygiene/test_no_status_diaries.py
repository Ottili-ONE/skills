"""The repository must not carry status diaries, and must not duplicate a skill.

Two invariants that the tree policy of SKL-W0-01 (TASK-0004) established:

1. **No status diaries.** A pass-by-pass diary (``STATUS.md``, ``HANDOFF*.md``,
   ``GAPS*.md``, ``R3_PLAN.md``, ``REVERIFY*.md``) goes stale the moment the
   product changes, and nothing reads it. The evidence a diary used to hold
   lives with the thing it describes: in the skill's ``references/SOURCES.md``,
   in ``docs/truth/REPAIR_LOG.md`` and in the job's ``.truth/`` log.
   ``references/EVALS.md`` is skill content, not a diary, and stays.

2. **One tree.** Every skill lives in exactly one directory. A second copy of a
   skill (the stale top-level ``business-de/`` was one) doubles the maintenance
   and lets the two copies drift apart.

The check reads the *tracked* files, so it also holds in a fresh clone.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: Basenames that are diaries. ``references/EVALS.md`` and the lowercase
#: ``references/handoff.md`` are skill content and are not listed here.
DIARY_NAME = re.compile(
    r"^(STATUS[^/]*\.md|HANDOFF[^/]*\.md|GAPS[^/]*\.md|R3_PLAN\.md|REVERIFY[^/]*\.md)$"
)


def tracked_paths() -> list[str]:
    """Every tracked path in the repository."""
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in out.stdout.splitlines() if line]


def test_no_status_diary_is_committed() -> None:
    """No tracked path may be a status/handoff/gaps/plan/reverify diary."""
    diaries = sorted(p for p in tracked_paths() if DIARY_NAME.match(Path(p).name))
    assert not diaries, f"status diaries are committed again: {diaries}"


def test_no_skill_directory_name_is_duplicated() -> None:
    """No two SKILL.md may live in directories with the same name."""
    out = subprocess.run(
        ["git", "ls-files", "*/SKILL.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    names = [Path(line).parent.name for line in out.stdout.splitlines() if line]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    assert not duplicates, f"duplicate skill directories: {duplicates}"


def test_no_stale_top_level_duplicate_package() -> None:
    """The stale top-level ``business-de/`` duplicate must not come back."""
    stale = sorted(p for p in tracked_paths() if p.startswith("business-de/"))
    assert not stale, f"the stale top-level business-de/ duplicate is back: {stale}"
