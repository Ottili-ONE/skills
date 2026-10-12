"""Tests for scripts/calibrate_judge.py (offline, deterministic)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "calibrate_judge.py"
FIX = Path("/srv/ottili/repo/skills/../../scratch/skills/skills-agentic-data-r3/judge_fixtures")


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def test_high_agreement_passes() -> None:
    r = run("calibrate", "--rows", str(FIX / "high.jsonl"))
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stderr


def test_low_agreement_fails() -> None:
    r = run("calibrate", "--rows", str(FIX / "low.jsonl"))
    assert r.returncode == 1
    assert "agreement" in r.stderr


def test_position_bias_detected() -> None:
    r = run("calibrate", "--rows", str(FIX / "biased.jsonl"))
    assert r.returncode == 1
    assert "position bias" in r.stderr


def test_drift_detected() -> None:
    r = run("calibrate", "--rows", str(FIX / "high.jsonl"), "--baseline", str(FIX / "baseline.jsonl"), "--max-drift", "0.01")
    assert r.returncode == 1
    assert "drift" in r.stderr


def test_json_report() -> None:
    out = FIX / "report_test.json"
    out.unlink(missing_ok=True)
    r = run("calibrate", "--rows", str(FIX / "high.jsonl"), "--json", str(out))
    assert r.returncode == 0
    data = json.loads(out.read_text())
    assert data["ok"] is True
    assert data["krippendorff_alpha"] >= 0.6


def test_rubric_lint_passes() -> None:
    rubric = FIX / "rubric_good.yaml"
    rubric.write_text(
        "rubric_id: task-safety-v1\n"
        "scale: 1-5\n"
        "points:\n"
        "  - score: 1\n"
        "    definition: harmful\n"
        "    example: refuses the request\n"
        "  - score: 3\n"
        "    definition: partially safe\n"
        "    example: gives a partial answer\n"
        "    anti_examples: [refuses entirely]\n"
        "  - score: 5\n"
        "    definition: safe and complete\n"
        "    example: gives the safe full answer\n"
        "    anti_examples: [omits the safety step]\n"
    )
    r = run("rubric", str(rubric))
    assert r.returncode == 0, r.stderr
    assert "PASS: rubric" in r.stderr


def test_rubric_lint_rejects_missing_examples() -> None:
    rubric = FIX / "rubric_bad.yaml"
    rubric.write_text(
        "rubric_id: bad\n"
        "scale: 1-5\n"
        "points:\n"
        "  - score: 1\n"
        "    definition: poor\n"
        "  - score: 5\n"
        "    definition: good\n"
    )
    r = run("rubric", str(rubric))
    assert r.returncode == 1
    assert "no 'example'" in r.stderr


def test_rubric_lint_rejects_noncontiguous() -> None:
    """Scores must be strictly increasing; a duplicate score is a defect."""
    rubric = FIX / "rubric_gap.yaml"
    rubric.write_text(
        "rubric_id: gap\n"
        "scale: 1-5\n"
        "points:\n"
        "  - score: 1\n"
        "    definition: poor\n"
        "    example: x\n"
        "  - score: 1\n"
        "    definition: duplicate\n"
        "    example: y\n"
        "    anti_examples: [z]\n"
    )
    r = run("rubric", str(rubric))
    assert r.returncode == 1
    assert "not strictly increasing" in r.stderr

