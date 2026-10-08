"""Tests for immutability_check.py: in-place modification, append-only, deletion."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "immutability_check.py"


def run(archive, state):
    r = subprocess.run([sys.executable, str(SCRIPT), "--archive", str(archive),
                        "--state", str(state)], capture_output=True, text=True)
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
