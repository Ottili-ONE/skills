"""Tests for immutability_check.py: in-place modification, append-only, deletion.

The checker is read-only by default (it must never mutate the archive state
during a check). The first run therefore needs --write-state to initialise the
chain; every subsequent run is a plain check and must not touch the state file.
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "immutability_check.py"


def run(archive, state, write=False):
    cmd = [sys.executable, str(SCRIPT), "--archive", str(archive), "--state", str(state)]
    if write:
        cmd.append("--write-state")
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout)


def test_first_run_requires_write_state(tmp_path):
    """A first run without --write-state reports the file as new and does NOT write."""
    archive = tmp_path / "a"
    archive.mkdir()
    (archive / "inv.xml").write_text("x")
    state = tmp_path / "s.json"
    code, out = run(archive, state)
    assert code == 0 and out["ok"]
    assert out["new_files"] == ["inv.xml"]
    assert not state.exists(), "read-only default must not create the state file"


def test_write_state_initialises_chain(tmp_path):
    archive = tmp_path / "a"
    archive.mkdir()
    (archive / "inv.xml").write_text("x")
    state = tmp_path / "s.json"
    code, out = run(archive, state, write=True)
    assert code == 0 and out["ok"]
    assert out["wrote_state"] is True
    assert state.exists()


def test_in_place_modification_detected(tmp_path):
    archive = tmp_path / "a"
    archive.mkdir()
    f = archive / "inv.xml"
    f.write_text("v1")
    state = tmp_path / "s.json"
    run(archive, state, write=True)
    f.write_text("v2")
    code, out = run(archive, state)
    assert code == 1 and not out["ok"]
    assert "inv.xml" in out["violations"]


def test_deletion_detected(tmp_path):
    archive = tmp_path / "a"
    archive.mkdir()
    (archive / "inv.xml").write_text("x")
    state = tmp_path / "s.json"
    run(archive, state, write=True)
    (archive / "inv.xml").unlink()
    code, out = run(archive, state)
    assert code == 1
    assert any("deleted" in v for v in out["violations"])


def test_append_only_is_not_a_violation(tmp_path):
    """Adding a file is fine without --strict; only in-place change or deletion is."""
    archive = tmp_path / "a"
    archive.mkdir()
    (archive / "inv.xml").write_text("x")
    state = tmp_path / "s.json"
    run(archive, state, write=True)
    (archive / "inv2.xml").write_text("y")
    code, out = run(archive, state)
    assert code == 0 and out["ok"]
    assert out["new_files"] == ["inv2.xml"]
