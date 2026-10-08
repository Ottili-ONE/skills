"""Tests for scripts/ledger.py (offline, deterministic)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ledger.py"
FIX = Path("/srv/ottili/repo/skills/../../scratch/skills/skills-agentic-data-r3/ledger_fixtures")


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def test_audit_clean() -> None:
    r = run("audit", str(FIX / "traj.jsonl"))
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stderr


def test_audit_rejects_fabricated_success() -> None:
    r = run("audit", str(FIX / "traj_bad.jsonl"))
    assert r.returncode == 1
    assert "evidence" in r.stderr


def test_audit_rejects_ungrounded_tool() -> None:
    r = run("audit", str(FIX / "traj_bad2.jsonl"))
    assert r.returncode == 1
    assert "result.exit_code" in r.stderr


def test_cost_sums() -> None:
    r = run("cost", str(FIX / "traj.jsonl"))
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["seconds"] == 0.1


def test_replay_matches() -> None:
    r = run("replay", str(FIX / "traj.jsonl"), str(FIX / "traj.jsonl"))
    assert r.returncode == 0
    assert "PASS" in r.stderr


def test_replay_diverges() -> None:
    r = run("replay", str(FIX / "traj.jsonl"), str(FIX / "traj_div.jsonl"))
    assert r.returncode == 1
    assert "diverges" in r.stderr
