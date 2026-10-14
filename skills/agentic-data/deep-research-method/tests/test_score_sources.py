"""Tests for scripts/score_sources.py (offline, deterministic)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "score_sources.py"
FIX = Path(__file__).resolve().parent / "fixtures"


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

def test_cite_emits_kept_sources() -> None:
    r = run("cite", str(FIX / "good.jsonl"))
    assert r.returncode == 0, r.stderr
    assert "europa.eu" in r.stderr
    assert "PASS: 3 citation" in r.stderr


def test_cite_drops_below_min() -> None:
    r = run("cite", str(FIX / "bad.jsonl"), "--min", "6")
    assert r.returncode == 1
    assert "no kept sources" in r.stderr


def test_cite_missing_file_exit_2() -> None:
    r = run("cite", str(FIX / "nope.jsonl"))
    assert r.returncode == 2
    assert "not found" in r.stderr


def test_fetch_lists_urls() -> None:
    r = run("fetch", str(FIX / "good.jsonl"))
    assert r.returncode == 0, r.stderr
    assert "europa.eu" in r.stdout
    assert "PASS: 3 fetch URL" in r.stderr


def test_fetch_empty_when_all_below_min() -> None:
    r = run("fetch", str(FIX / "bad.jsonl"), "--min", "6")
    assert r.returncode == 1
    assert "no kept sources" in r.stderr


def test_staleness_flags_old_source() -> None:
    stale = FIX / "stale.jsonl"
    stale.write_text(
        '{"url": "https://arxiv.org/abs/2212.08073", "authority": 3, "recency": 2, '
        '"corroboration": 3, "retrieved": "2024-01-01", "version": "v1"}\n'
        '{"url": "https://openai.com/index/evals/", "authority": 3, "recency": 3, '
        '"corroboration": 3, "retrieved": "2026-10-09", "version": "HEAD"}\n'
    )
    r = run("staleness", str(stale), "--question-date", "2026-10-12")
    assert r.returncode == 1
    assert "stale" in r.stderr
    assert "2024-01-01" in r.stderr


def test_staleness_clean_within_window() -> None:
    r = run("staleness", str(FIX / "good.jsonl"), "--question-date", "2026-10-12")
    assert r.returncode == 0, r.stderr
    assert "PASS: no source is older than" in r.stderr


def test_staleness_rejects_bad_question_date() -> None:
    r = run("staleness", str(FIX / "good.jsonl"), "--question-date", "not-a-date")
    assert r.returncode == 1
    assert "invalid question date" in r.stderr


def test_corroboration_passes_on_independent_upstreams() -> None:
    r = run("corroboration", str(FIX / "good.jsonl"))
    assert r.returncode == 0, r.stderr
    assert "independent upstream" in r.stderr


def test_corrobocation_flags_shared_upstream() -> None:
    shared = FIX / "shared.jsonl"
    shared.write_text(
        '{"url": "https://arxiv.org/abs/2212.08073", "authority": 3, "recency": 3, '
        '"corroboration": 3, "retrieved": "2026-10-09", "version": "v1", '
        '"upstream": "https://arxiv.org/abs/2212.08073"}\n'
        '{"url": "https://blog.example.com/ai-safety", "authority": 1, "recency": 3, '
        '"corroboration": 3, "retrieved": "2026-10-09", "version": "2026", '
        '"upstream": "https://arxiv.org/abs/2212.08073"}\n'
    )
    r = run("corroboration", str(shared))
    assert r.returncode == 1
    assert "share upstream" in r.stderr


def test_provenance_passes_when_all_fields_present() -> None:
    r = run("provenance", str(FIX / "good.jsonl"))
    assert r.returncode == 0, r.stderr
    assert "URL + retrieval date + version" in r.stderr


def test_provenance_flags_missing_version() -> None:
    noversion = FIX / "noversion.jsonl"
    noversion.write_text(
        '{"url": "https://www.europa.eu/legal-summary/", "authority": 4, "recency": 3, '
        '"corroboration": 3, "retrieved": "2026-10-09"}\n'
    )
    r = run("provenance", str(noversion))
    assert r.returncode == 1
    assert "no pinned 'version'" in r.stderr


def test_provenance_flags_missing_date() -> None:
    nodate = FIX / "nodate.jsonl"
    nodate.write_text(
        '{"url": "https://arxiv.org/abs/2212.08073", "authority": 3, "recency": 3, '
        '"corroboration": 3, "version": "v1"}\n'
    )
    r = run("provenance", str(nodate))
    assert r.returncode == 1
    assert "no 'retrieved' date" in r.stderr



def test_confidence_medium_single_upstream() -> None:
    # single.jsonl keeps one source tracing to one upstream -> medium
    r = run("confidence", str(FIX / "single.jsonl"))
    assert r.returncode == 0, r.stderr
    assert '"confidence": "medium"' in r.stdout


def test_confidence_high_three_upstreams() -> None:
    # good.jsonl keeps three sources across three distinct upstreams -> high
    r = run("confidence", str(FIX / "good.jsonl"))
    assert r.returncode == 0, r.stderr
    assert '"confidence": "high"' in r.stdout


def test_confidence_fake_middle_is_medium() -> None:
    # equal.jsonl keeps two URLs that share one upstream: the fake middle.
    # Confidence is medium, not high, because there is one upstream.
    r = run("confidence", str(FIX / "equal.jsonl"))
    assert r.returncode == 0, r.stderr
    assert '"confidence": "medium"' in r.stdout
    assert '"n_upstreams": 1' in r.stdout


def test_confidence_rejects_no_kept_sources() -> None:
    r = run("confidence", str(FIX / "bad.jsonl"))
    assert r.returncode == 1
    assert "no kept sources" in r.stderr


def test_help_lists_subcommands() -> None:
    r = run("--help")
    assert r.returncode == 0
    for sub in ("score", "audit", "contradictions", "corroboration",
                "provenance", "cite", "fetch", "staleness", "confidence"):
        assert sub in r.stdout, f"missing subcommand {sub}"
