"""Tests for immutability_check.py: in-place modification, append-only, deletion."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "immutability_check.py"


def run(archive, state, *extra):
    """Default run seeds the state on first invocation (``--init-state``).

    The script is read-only by default, so a baseline must be created
    explicitly; the helper mirrors the documented first-run workflow.
    """
    r = subprocess.run([sys.executable, str(SCRIPT), "--archive", str(archive),
                        "--state", str(state), "--init-state", *extra],
                       capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout)


def test_first_run_records_state(tmp_path):
    archive = tmp_path / "a"
    archive.mkdir()
    (archive / "inv.xml").write_text("x")
    state = tmp_path / "s.json"
    code, out = run(archive, state)
    assert code == 0 and out["ok"]
    assert out["new_files"] == ["inv.xml"]
    assert state.exists()


def test_in_place_modification_detected(tmp_path):
    archive = tmp_path / "a"
    archive.mkdir()
    f = archive / "inv.xml"
    f.write_text("v1")
    state = tmp_path / "s.json"
    run(archive, state)
    f.write_text("v2")
    code, out = run(archive, state)
    assert code == 1 and not out["ok"]
    assert "inv.xml" in out["violations"]


def test_deletion_detected(tmp_path):
    archive = tmp_path / "a"
    archive.mkdir()
    (archive / "inv.xml").write_text("x")
    state = tmp_path / "s.json"
    run(archive, state)
    (archive / "inv.xml").unlink()
    code, out = run(archive, state)
    assert code == 1
    assert any("deleted" in v for v in out["violations"])


def test_read_only_by_default_does_not_write_state(tmp_path):
    """The default run must not modify the state file (a GoBD audit check
    must not rewrite the archive's own bookkeeping)."""
    archive = tmp_path / "a"
    archive.mkdir()
    (archive / "inv.xml").write_text("x")
    state = tmp_path / "s.json"
    run(archive, state)
    mtime_before = state.stat().st_mtime_ns
    run(archive, state)  # second run, no --write-state
    assert state.stat().st_mtime_ns == mtime_before


def test_write_state_opt_in(tmp_path):
    archive = tmp_path / "a"
    archive.mkdir()
    (archive / "inv.xml").write_text("x")
    state = tmp_path / "s.json"
    run(archive, state)
    mtime_before = state.stat().st_mtime_ns
    r = subprocess.run([sys.executable, str(SCRIPT), "--archive", str(archive),
                        "--state", str(state), "--write-state"],
                       capture_output=True, text=True)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["state_written"] is True
    assert state.stat().st_mtime_ns != mtime_before


def test_strict_rejects_new_files(tmp_path):
    archive = tmp_path / "a"
    archive.mkdir()
    (archive / "inv.xml").write_text("x")
    state = tmp_path / "s.json"
    run(archive, state)
    (archive / "new.xml").write_text("y")
    r = subprocess.run([sys.executable, str(SCRIPT), "--archive", str(archive),
                        "--state", str(state), "--strict"], capture_output=True, text=True)
    code, out = r.returncode, json.loads(r.stdout)
    assert code == 1
    assert any("new files" in v for v in out["violations"])
