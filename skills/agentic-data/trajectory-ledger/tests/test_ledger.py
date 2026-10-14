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


def test_normalize_recomputes_hashes() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "norm.jsonl"
        r = run("normalize", str(FIX / "traj.jsonl"), str(out))
        assert r.returncode == 0, r.stderr
        assert "PASS: normalised" in r.stderr
        assert out.is_file()
        # the normalised file must still audit clean
        r2 = run("audit", str(out))
        assert r2.returncode == 0, r2.stderr


def test_normalize_rejects_malformed() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "bad.jsonl"
        bad.write_text('{"step": 0, "type": "think"}\nnot json\n')
        out = Path(td) / "norm.jsonl"
        # load_events raises SystemExit(1) on a malformed line, so the
        # process exits non-zero with the message on stderr.
        r = run("normalize", str(bad), str(out))
        assert r.returncode != 0
        assert "not valid JSON" in r.stderr or "not a JSON object" in r.stderr


def test_record_non_det_appends_observe_event() -> None:
    import tempfile, json
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "norm.jsonl"
        run("normalize", str(FIX / "traj.jsonl"), str(out))
        # the divergence was at step 1; the record itself is a new event and
        # must be appended after the last recorded step (2 here).
        r = run("record-non-det", str(out), "3", "timestamps drifted")
        assert r.returncode == 0, r.stderr
        assert "recorded non-determinism" in r.stderr
        lines = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
        assert any(e.get("non_determinism") is True for e in lines)
        # the appended event must be the last step and audit clean
        assert lines[-1]["step"] == 3
        assert lines[-1]["non_determinism"] is True
        # and the appended event must audit clean
        r2 = run("audit", str(out))
        assert r2.returncode == 0, r2.stderr


def test_audit_rejects_unordered_steps() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "unordered.jsonl"
        p.write_text(
            '{"schema": "trajectory-ledger-v1", "step": 0, "timestamp": "2026-10-09T12:00:00Z", '
            '"type": "think", "state": {"i": 0}, "state_hash": "sha256:0", '
            '"cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}}\n'
            '{"schema": "trajectory-ledger-v1", "step": 2, "timestamp": "2026-10-09T12:00:02Z", '
            '"type": "think", "state": {"i": 2}, "state_hash": "sha256:0", '
            '"cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}}\n'
            '{"schema": "trajectory-ledger-v1", "step": 1, "timestamp": "2026-10-09T12:00:01Z", '
            '"type": "think", "state": {"i": 1}, "state_hash": "sha256:0", '
            '"cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}}\n'
        )
        r = run("audit", str(p))
        assert r.returncode == 1
        assert "not strictly greater" in r.stderr


def test_audit_rejects_missing_schema() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "noschema.jsonl"
        p.write_text(
            '{"step": 0, "timestamp": "2026-10-09T12:00:00Z", "type": "think", '
            '"state": {"i": 0}, "state_hash": "sha256:0", '
            '"cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}}\n'
        )
        r = run("audit", str(p))
        assert r.returncode == 1
        assert "no event declares schema" in r.stderr


def test_audit_rejects_mixed_schema_versions() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "mixed.jsonl"
        p.write_text(
            '{"schema": "trajectory-ledger-v1", "step": 0, "timestamp": "2026-10-09T12:00:00Z", '
            '"type": "think", "state": {"i": 0}, "state_hash": "sha256:0", '
            '"cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}}\n'
            '{"schema": "draft-v9", "step": 1, "timestamp": "2026-10-09T12:00:01Z", '
            '"type": "think", "state": {"i": 1}, "state_hash": "sha256:0", '
            '"cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}}\n'
        )
        r = run("audit", str(p))
        assert r.returncode == 1
        assert "mixes schema versions" in r.stderr


def test_record_non_det_rejects_out_of_order_step() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "norm.jsonl"
        run("normalize", str(FIX / "traj.jsonl"), str(out))
        # the last recorded step is 2; step 1 is not strictly greater
        r = run("record-non-det", str(out), "1", "timestamps drifted")
        assert r.returncode == 1
        assert "not strictly greater" in r.stderr


def test_cost_max_usd_rejects_overrun() -> None:
    # The shipped fixture has usd=0.0, so --max-usd 0 is the boundary: a
    # strictly-positive budget is required for a real run.
    r = run("cost", str(FIX / "traj.jsonl"), "--max-usd", "0")
    assert r.returncode == 1
    assert "exceeds --max-usd" in r.stderr


def test_cost_max_seconds_rejects_overrun() -> None:
    r = run("cost", str(FIX / "traj.jsonl"), "--max-seconds", "0.01")
    assert r.returncode == 1
    assert "exceeds --max-seconds" in r.stderr


def test_cost_budget_accepts_within() -> None:
    r = run("cost", str(FIX / "traj.jsonl"), "--max-usd", "1.0", "--max-seconds", "1.0")
    assert r.returncode == 0, r.stderr
    assert "cost within budget" in r.stderr


def test_audit_strict_rejects_partial_cost() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "partial.jsonl"
        p.write_text(
            '{"schema": "trajectory-ledger-v1", "step": 0, "timestamp": "2026-10-09T12:00:00Z", '
            '"type": "think", "state": {"i": 0}, "state_hash": "sha256:0", '
            '"cost": {"tokens_in": 1, "tokens_out": 1}}\n'
        )
        r = run("audit", str(p), "--strict")
        assert r.returncode == 1
        assert "no unit" in r.stderr


def test_audit_strict_accepts_complete_cost() -> None:
    r = run("audit", str(FIX / "traj.jsonl"), "--strict")
    assert r.returncode == 0, r.stderr


def test_audit_max_usd_rejects_overrun() -> None:
    r = run("audit", str(FIX / "traj.jsonl"), "--max-usd", "0")
    assert r.returncode == 1
    assert "exceeds --max-usd" in r.stderr
