"""Tests for scripts/score_sources.py (offline, deterministic)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "score_sources.py"
FIX = Path("/srv/ottili/repo/skills/../../scratch/skills/skills-agentic-data-r3/deepr_fixtures")


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def test_good_sources_pass() -> None:
    r = run("score", str(FIX / "good.jsonl"))
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stderr


def test_bad_sources_fail() -> None:
    r = run("score", str(FIX / "bad.jsonl"))
    assert r.returncode == 1
    assert "score 2 < 6" in r.stderr
    assert "retrieved" in r.stderr


def test_missing_date_rejected() -> None:
    r = run("score", str(FIX / "bad.jsonl"))
    assert r.returncode == 1
    assert "invalid 'retrieved'" in r.stderr


def test_audit_good_claims() -> None:
    r = run("audit", str(FIX / "good.jsonl"), str(FIX / "claims.json"))
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stderr


def test_audit_rejects_uncited_claim() -> None:
    claims = {"claims": [{"text": "x", "cites": []}]}
    out = FIX / "claims_uncited.json"
    out.write_text(json.dumps(claims))
    r = run("audit", str(FIX / "good.jsonl"), str(out))
    assert r.returncode == 1
    assert "cites no source" in r.stderr


def test_audit_rejects_discarded_source() -> None:
    r = run("audit", str(FIX / "good.jsonl"), str(FIX / "claims_bad.json"))
    assert r.returncode == 1
    assert "not kept" in r.stderr
