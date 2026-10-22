#!/usr/bin/env python3
"""The sign-off contract of the six UNVERIFIED reference wrappers.

Every wrapper stays at the ``UNVERIFIED`` sentinel until an adviser fills the
sign-off block of its review file. The wrappers name the audit that enforces
this and point at the review file the audit reads. The suite covers all six
wrappers; it lives with the wrapper whose review file carries the most content
(the two legal corrections that are under sign-off).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILLS = ROOT / "skills"
REVIEWS = ROOT / "docs" / "reviews"
AUDIT = ROOT / "scripts" / "validate_reviewed_by.py"

WRAPPERS = (
    "ref-bank-reconciliation-camt",
    "ref-datev-extf",
    "ref-gobd-archive",
    "ref-ust-edge-cases",
    "ref-webhooks-safe",
    "ref-xrechnung-zugferd",
)

GATE_COMMAND = "python3 scripts/validate_reviewed_by.py"
BLOCK_LINES = ("Reviewed by:", "Date:", "Signature:")


def wrapper_skill(name: str) -> Path:
    """The SKILL.md of a wrapper package."""
    return SKILLS / name / name / "SKILL.md"


def test_every_wrapper_is_marked_unverified() -> None:
    """No wrapper claims a reviewer."""
    for name in WRAPPERS:
        text = wrapper_skill(name).read_text(encoding="utf-8")
        assert re.search(r"^reviewed_by: UNVERIFIED$", text, flags=re.MULTILINE), (
            f"{name} must stay at the UNVERIFIED sentinel"
        )


def test_every_wrapper_names_the_audit_that_enforces_the_gate() -> None:
    """The wrappers point at the audit that decides whether a sign-off counts."""
    for name in WRAPPERS:
        text = wrapper_skill(name).read_text(encoding="utf-8")
        assert GATE_COMMAND in text, f"{name} does not name the sign-off audit"


def test_every_wrapper_points_at_its_own_review_file() -> None:
    """Each wrapper names the review file the audit reads for it."""
    for name in WRAPPERS:
        text = wrapper_skill(name).read_text(encoding="utf-8")
        assert f"docs/reviews/{name}.md" in text, f"{name} does not name its review file"


def test_every_review_file_carries_the_unfilled_sign_off_block() -> None:
    """Each review file carries the markers the audit reads, all unfilled."""
    for name in WRAPPERS:
        text = (REVIEWS / f"{name}.md").read_text(encoding="utf-8")
        assert "Status: UNVERIFIED" in text, f"{name} review is not marked UNVERIFIED"
        assert re.search(r"\|\s*Date\s*\|\s*\*\*pending\*\*\s*\|", text), (
            f"{name} review does not carry the pending date marker"
        )
        for line in BLOCK_LINES:
            assert re.search(rf"^{re.escape(line)}\s*_+", text, flags=re.MULTILINE), (
                f"{name} review does not carry an unfilled {line} line"
            )


def test_the_audit_reports_the_six_wrappers_as_unverified() -> None:
    """The audit sees the six wrappers and certifies nothing."""
    result = subprocess.run(
        [sys.executable, str(AUDIT), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["ok"], report["problems"]
    assert sorted(entry["skill"] for entry in report["unverified"]) == sorted(WRAPPERS)
    assert report["certified"] == [], "no wrapper may be certified before the sign-off"
