"""Near-miss trigger tests for period_lock.py (the actual lock script).

The traps: locking without an approver, overriding without evidence,
unlocking an unlocked period, and a malformed period string.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "period_lock.py"
EV = Path(__file__).resolve().parent / "test_journal_check.py"


def run(args, state):
    r = subprocess.run([sys.executable, str(SCRIPT), *args, "--state", str(state)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def test_lock_requires_approver():
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "p.json"
        rc, out = run(["--period", "2026-12", "--action", "lock"], state)
        assert rc == 1 and "approver" in out


def test_override_without_evidence_blocked():
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "p.json"
        run(["--period", "2026-12", "--action", "lock",
             "--approver", "M. Braun", "--reason", "close"], state)
        rc, out = run(["--period", "2026-12", "--action", "override",
                       "--approver", "agent", "--reason", "fix"], state)
        assert rc == 1 and "evidence" in out


def test_override_on_unlocked_period_blocked():
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "p.json"
        rc, out = run(["--period", "2026-12", "--action", "override",
                       "--approver", "agent", "--evidence", str(EV)], state)
        assert rc == 1 and "not locked" in out


def test_unlock_on_unlocked_period_blocked():
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "p.json"
        rc, out = run(["--period", "2026-12", "--action", "unlock",
                       "--approver", "agent"], state)
        assert rc == 1 and "not locked" in out


def test_bad_period_rejected():
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "p.json"
        rc, out = run(["--period", "2026-1", "--action", "status"], state)
        assert rc == 1 and "YYYYMM" in out


def test_status_reports_history():
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "p.json"
        run(["--period", "2026-12", "--action", "lock",
             "--approver", "M. Braun", "--reason", "Monatsschluss",
             "--evidence", str(EV)], state)
        rc, out = run(["--period", "2026-12", "--action", "status"], state)
        assert rc == 0
        data = json.loads(out)
        assert data["locked"] is True
        assert data["locked_by"] == "M. Braun"
        assert any(h["action"] == "lock" for h in data["history"])
