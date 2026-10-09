import json, subprocess, sys, tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "period_lock_check.py"
EV = Path(__file__).resolve().parent / "test_journal_check.py"  # real file, reused as evidence


def run(args, state):
    r = subprocess.run([sys.executable, str(SCRIPT), *args, "--state", str(state)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def test_status_open():
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "p.json"
        rc, out = run(["status"], state)
        assert rc == 1 and '"locked": false' in out


def test_check_not_locked():
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "p.json"
        rc, _ = run(["check"], state)
        assert rc == 2


def test_lock_requires_evidence():
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "p.json"
        rc, out = run(["lock", "--period", "2026-12", "--approved-by", "M. Braun",
                       "--reason", "Monatsschluss"], state)
        assert rc == 2 and "evidence" in out


def test_lock_and_check_clean():
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "p.json"
        rc, _ = run(["lock", "--period", "2026-12", "--approved-by", "M. Braun",
                     "--reason", "Monatsschluss", "--evidence", str(EV)], state)
        assert rc == 0
        rc, out = run(["check"], state)
        assert rc == 0 and "no override" in out
        data = json.loads(state.read_text())
        assert data["locked"] is True and data["period"] == "2026-12"


def test_unlock_requires_evidence():
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "p.json"
        run(["lock", "--period", "2026-12", "--approved-by", "M. Braun",
             "--reason", "Monatsschluss", "--evidence", str(EV)], state)
        rc, out = run(["unlock", "--by", "agent", "--reason", "x"], state)
        assert rc == 2 and "evidence" in out


def test_unlock_logs_override_and_check_flags_it():
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "p.json"
        run(["lock", "--period", "2026-12", "--approved-by", "M. Braun",
             "--reason", "Monatsschluss", "--evidence", str(EV)], state)
        rc, _ = run(["unlock", "--by", "agent", "--reason", "correcting entry",
                     "--evidence", str(EV)], state)
        assert rc == 0
        # after unlock the period is open again -> check returns 2, not 1
        rc, out = run(["check"], state)
        assert rc == 2 and "not locked" in out
        rc, out = run(["history"], state)
        assert rc == 0 and "correcting entry" in out
