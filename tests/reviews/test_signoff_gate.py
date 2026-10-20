"""Exercises scripts/validate_reviewed_by.py (SKL-W1-02 TASK-0002).

The UNVERIFIED sentinel, the filled-signoff certifier and the fail-closed
cases.

Converted from ``test_signoff_gate.test.mjs`` to pytest: the gate runs
``pytest -q {paths}`` and a ``*.test.mjs`` file cannot be collected by pytest.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VALIDATOR = REPO / "scripts" / "validate_reviewed_by.py"
REVIEWS = REPO / "docs" / "reviews"

NAMES = (
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


def frontmatter(name: str) -> dict[str, str]:
    """Read the frontmatter of a skill's SKILL.md without a YAML dependency."""
    md = REPO / "skills" / name / name / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n([\s\S]*?)\n---\s*\n", text)
    assert match, f"no frontmatter in {md}"
    fields: dict[str, str] = {}
    for line in match.group(1).split("\n"):
        key, separator, value = line.partition(":")
        if not separator:
            continue
        fields[key.strip()] = value.strip().strip("\"'")
    return fields


def test_all_six_ref_wrappers_carry_reviewed_by_unverified() -> None:
    """All six ref-* wrappers carry reviewed_by: UNVERIFIED."""
    for name in NAMES:
        assert frontmatter(name).get("reviewed_by") == "UNVERIFIED", name


def test_audit_reports_the_six_wrappers_as_unverified_and_exits_zero() -> None:
    """The audit reports the six wrappers as unverified and exits 0."""
    result = audit("--json")
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    unverified = [entry["skill"] for entry in report["unverified"]]
    for name in NAMES:
        assert name in unverified, f"{name} not reported unverified"
    assert report["problems"] == [], json.dumps(report["problems"])


def test_unverified_skills_never_block() -> None:
    """UNVERIFIED skills never block: the non-strict audit exits 0."""
    result = audit()
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_filled_sign_off_block_certifies_the_skill() -> None:
    """A filled sign-off block certifies the skill (audit exits 0, entry ok)."""
    file = REVIEWS / "ref-ust-edge-cases.md"
    backup = file.read_text(encoding="utf-8")
    filled = (
        backup.replace(
            "| Reviewed by | **UNVERIFIED — pending signature** |",
            "| Reviewed by | Dr. Anna Meier |",
        )
        .replace("| Date | **pending** |", "| Date | 2026-10-16 |")
        .replace("Date: _______________", "Date: 2026-10-16")
        .replace("Reviewed by: ___________________________________", "Reviewed by: Dr. Anna Meier")
        .replace("Signature: ___________________________________", "Signature: Dr. Anna Meier")
        .replace(
            "Findings: ___________________________________",
            "Findings: §13b scope and igL citation confirmed correct",
        )
    )
    md = REPO / "skills" / "ref-ust-edge-cases" / "ref-ust-edge-cases" / "SKILL.md"
    md_backup = md.read_text(encoding="utf-8")
    try:
        md.write_text(
            re.sub(r"^reviewed_by: UNVERIFIED$", "reviewed_by: Dr. Anna Meier", md_backup, flags=re.MULTILINE),
            encoding="utf-8",
        )
        file.write_text(filled, encoding="utf-8")
        result = audit("--json")
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads(result.stdout)
        certified = [entry for entry in report["certified"] if entry["skill"] == "ref-ust-edge-cases"]
        assert certified, "ref-ust-edge-cases not certified"
        assert certified[0]["ok"] is True
    finally:
        file.write_text(backup, encoding="utf-8")
        md.write_text(md_backup, encoding="utf-8")


def test_a_certified_skill_with_an_empty_sign_off_block_is_a_problem() -> None:
    """A certified skill with an empty sign-off block is a problem."""
    file = REVIEWS / "ref-ust-edge-cases.md"
    backup = file.read_text(encoding="utf-8")
    empty = (
        backup.replace(
            "| Reviewed by | **UNVERIFIED — pending signature** |",
            "| Reviewed by | Dr. Anna Meier |",
        )
        .replace(
            "Reviewed by: ___________________________________",
            "Reviewed by: ___________________________________",
        )
        .replace("Date: _______________", "Date: _______________")
        .replace("Signature: ___________________________________", "Signature: ___________________________________")
    )
    md = REPO / "skills" / "ref-ust-edge-cases" / "ref-ust-edge-cases" / "SKILL.md"
    md_backup = md.read_text(encoding="utf-8")
    try:
        md.write_text(
            re.sub(r"^reviewed_by: UNVERIFIED$", "reviewed_by: Dr. Anna Meier", md_backup, flags=re.MULTILINE),
            encoding="utf-8",
        )
        file.write_text(empty, encoding="utf-8")
        result = audit("--json")
        assert result.returncode != 0, (
            "audit should fail when a certified skill has an empty sign-off block"
        )
    finally:
        file.write_text(backup, encoding="utf-8")
        md.write_text(md_backup, encoding="utf-8")


def test_a_certified_skill_whose_review_file_is_missing_is_a_problem() -> None:
    """A certified skill whose review file is missing is a problem."""
    md = REPO / "skills" / "ref-ust-edge-cases" / "ref-ust-edge-cases" / "SKILL.md"
    review = REVIEWS / "ref-ust-edge-cases.md"
    md_backup = md.read_text(encoding="utf-8")
    review_backup = review.read_text(encoding="utf-8")
    stash = review.with_name(review.name + ".missing-stash")
    try:
        md.write_text(
            re.sub(r"^reviewed_by: UNVERIFIED$", "reviewed_by: Dr. Anna Meier", md_backup, flags=re.MULTILINE),
            encoding="utf-8",
        )
        review.rename(stash)
        result = audit("--json")
        assert result.returncode != 0, "audit should fail when a certified skill has no sign-off file"
    finally:
        stash.rename(review)
        md.write_text(md_backup, encoding="utf-8")
        review.write_text(review_backup, encoding="utf-8")
