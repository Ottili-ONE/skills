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
    r = run("--rows", str(FIX / "high.jsonl"))
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stderr


def test_low_agreement_fails() -> None:
    r = run("--rows", str(FIX / "low.jsonl"))
    assert r.returncode == 1
    assert "agreement" in r.stderr


def test_position_bias_detected() -> None:
    r = run("--rows", str(FIX / "biased.jsonl"))
    assert r.returncode == 1
    assert "position bias" in r.stderr


def test_drift_detected() -> None:
    r = run("--rows", str(FIX / "high.jsonl"), "--baseline", str(FIX / "baseline.jsonl"), "--max-drift", "0.01")
    assert r.returncode == 1
    assert "drift" in r.stderr


def test_json_report() -> None:
    out = FIX / "report_test.json"
    out.unlink(missing_ok=True)
    r = run("--rows", str(FIX / "high.jsonl"), "--json", str(out))
    assert r.returncode == 0
    data = json.loads(out.read_text())
    assert data["ok"] is True
    assert data["krippendorff_alpha"] >= 0.6
