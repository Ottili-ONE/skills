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
