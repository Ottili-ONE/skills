"""Failure-path tests for scripts/validate_reviewed_by.py (SKL-W1-02 TASK-0004).

The validator must never crash on malformed input: a SKILL.md with broken
frontmatter or a truncated sign-off file must be reported, never certified, and
the audit must still exit 0 (fail-closed on certification, fail-open on parsing).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "validate_reviewed_by.py"
MD = REPO / "skills" / "ref-datev-extf" / "ref-datev-extf" / "SKILL.md"
REVIEW = REPO / "docs" / "reviews" / "ref-datev-extf.md"


def audit(args: tuple[str, ...] = ("--json",)) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO, capture_output=True, text=True, check=False,
    )


def test_corrupt_frontmatter_is_not_certified_and_audit_exits_zero() -> None:
    """Broken YAML frontmatter must not certify the skill and must not crash."""
    backup = MD.read_text()
    MD.write_text("---\nname: x\nreviewed_by: UNVERIFIED\nno closing fence")
    try:
        r = audit()
        assert r.returncode == 0, r.stderr
        report = json.loads(r.stdout)
        assert report["certified"] == [], "corrupt frontmatter must not certify anything"
        assert report["ok"] is True
    finally:
        MD.write_text(backup)


def test_truncated_review_file_is_not_certified_and_audit_exits_zero() -> None:
    """A truncated sign-off file must not certify the skill and must not crash."""
    backup = REVIEW.read_text()
    REVIEW.write_text("# truncated sign-off file\n")
    try:
        r = audit()
        assert r.returncode == 0, r.stderr
        report = json.loads(r.stdout)
        assert report["certified"] == []
        assert report["ok"] is True
    finally:
        REVIEW.write_text(backup)


def test_audit_json_is_machine_readable_and_counts_skills() -> None:
    """The --json report must enumerate every skill and stay deterministic."""
    r = audit()
    assert r.returncode == 0
    report = json.loads(r.stdout)
    assert report["skills"] >= 39
    assert "unverified" in report
    assert "problems" in report
    # Re-run: the report must be byte-identical (deterministic).
    r2 = audit()
    assert r2.stdout == r.stdout
