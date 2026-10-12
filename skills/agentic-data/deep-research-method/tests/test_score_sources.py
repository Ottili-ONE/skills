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


def test_contradictions_resolved_by_weight() -> None:
    pairs = FIX / "contradictions.json"
    r = run("contradictions", str(FIX / "good.jsonl"), str(pairs))
    assert r.returncode == 0, r.stderr
    assert "wins (score" in r.stderr


def test_contradictions_unknown_source_fails() -> None:
    pairs = FIX / "contradictions_bad.json"
    pairs.write_text(json.dumps([{"a": "https://nope.example/x", "b": "https://www.europa.eu/legal-summary/", "claim_a": "x", "claim_b": "y"}]))
    r = run("contradictions", str(FIX / "good.jsonl"), str(pairs))
    assert r.returncode == 1
    assert "unknown source" in r.stderr


def test_contradictions_equal_scores_unresolved() -> None:
    pairs = FIX / "contradictions_equal.json"
    pairs.write_text(json.dumps([{"a": "https://arxiv.org/abs/2212.08073", "b": "https://openai.com/index/evals/", "claim_a": "x", "claim_b": "y"}]))
    r = run("contradictions", str(FIX / "equal.jsonl"), str(pairs))
    assert r.returncode == 1
    assert "UNRESOLVED" in r.stderr


def test_audit_accepts_jsonl_claims() -> None:
    """The audit subcommand must accept one-claim-per-line JSONL, not only JSON."""
    out = FIX / "claims_jsonl.jsonl"
    out.write_text(json.dumps({"text": "a", "cites": ["https://www.europa.eu/legal-summary/"]})
                   + "\n"
                   + json.dumps({"text": "b", "cites": ["https://arxiv.org/abs/2212.08073"]}))
    r = run("audit", str(FIX / "good.jsonl"), str(out))
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stderr


def test_audit_rejects_empty_claims_file() -> None:
    out = FIX / "claims_empty.jsonl"
    out.write_text("")
    r = run("audit", str(FIX / "good.jsonl"), str(out))
    assert r.returncode == 1
    assert "empty" in r.stderr
