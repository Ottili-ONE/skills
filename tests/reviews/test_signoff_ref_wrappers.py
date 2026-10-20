"""Every ref-* wrapper carries reviewed_by: UNVERIFIED (SKL-W1-02 TASK-0004).

The validator refuses certified status without ``docs/reviews/<skill>.md``.

Converted from ``test_signoff_ref_wrappers.test.mjs`` to pytest: the gate runs
``pytest -q {paths}`` and a ``*.test.mjs`` file cannot be collected by pytest.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILLS = REPO / "skills"
REVIEWS = REPO / "docs" / "reviews"
VALIDATOR = REPO / "scripts" / "validate_reviewed_by.py"

WRAPPERS = (
    "ref-datev-extf",
    "ref-gobd-archive",
    "ref-xrechnung-zugferd",
    "ref-ust-edge-cases",
    "ref-bank-reconciliation-camt",
    "ref-webhooks-safe",
)


def audit(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the validator and return the result instead of raising on failure."""
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("name", WRAPPERS)
def test_wrapper_is_marked_reviewed_by_unverified(name: str) -> None:
    """Every ref-* wrapper is marked reviewed_by: UNVERIFIED."""
    text = (SKILLS / name / name / "SKILL.md").read_text(encoding="utf-8")
    assert re.search(r"^reviewed_by: UNVERIFIED$", text, flags=re.MULTILINE), (
        f"{name} must stay at the UNVERIFIED sentinel"
    )


@pytest.mark.parametrize("name", WRAPPERS)
def test_wrapper_has_a_sign_off_placeholder_under_docs_reviews(name: str) -> None:
    """Every ref-* wrapper has a sign-off placeholder under docs/reviews/."""
    text = (REVIEWS / f"{name}.md").read_text(encoding="utf-8")
    assert "Status: UNVERIFIED" in text
    assert "UNVERIFIED — pending signature" in text, (
        f"{name} review must carry the UNVERIFIED — pending signature marker"
    )
    assert re.search(r"\|\s*Date\s*\|\s*\*\*pending\*\*\s*\|", text), (
        f"{name} review must carry the pending date marker"
    )


def test_the_audit_reports_all_six_wrappers_as_unverified_and_exits_zero() -> None:
    """The audit reports all six wrappers as unverified and exits 0."""
    result = audit("--json")
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["ok"], f"audit problems: {json.dumps(report['problems'])}"
    names = sorted(entry["skill"] for entry in report["unverified"])
    assert names == sorted(WRAPPERS)


def test_a_wrapper_promoted_to_certified_without_a_filled_sign_off_block_fails() -> None:
    """A wrapper promoted to certified without a filled sign-off block fails."""
    md = SKILLS / "ref-ust-edge-cases" / "ref-ust-edge-cases" / "SKILL.md"
    review = REVIEWS / "ref-ust-edge-cases.md"
    md_backup = md.read_text(encoding="utf-8")
    review_backup = review.read_text(encoding="utf-8")
    empty = (
        review_backup.replace(
            "Reviewed by: **UNVERIFIED — pending signature**",
            "Reviewed by: Dr. Anna Meier",
        )
        .replace("Date: **pending**", "Date: 2026-10-16")
        .replace("Signature: ___________________________________", "Signature: ___________________________________")
    )
    try:
        md.write_text(
            re.sub(r"^reviewed_by: UNVERIFIED$", "reviewed_by: Dr. Anna Meier", md_backup, flags=re.MULTILINE),
            encoding="utf-8",
        )
        review.write_text(empty, encoding="utf-8")
        result = audit("--json")
        assert result.returncode != 0, (
            "audit must fail when a certified wrapper has an empty sign-off block"
        )
    finally:
        md.write_text(md_backup, encoding="utf-8")
        review.write_text(review_backup, encoding="utf-8")
