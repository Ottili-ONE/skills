"""Tests for audit_export.py: export, manifest, verify, empty source."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "audit_export.py"


def run(args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    blob = (r.stdout + r.stderr).strip()
    return r.returncode, (json.loads(blob) if blob else {"ok": False, "error": "no output"})


def test_export_writes_manifest(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "inv.xml").write_text("<x/>")
    out = tmp_path / "out"
    code, out_json = run(["--source", str(src), "--output", str(out), "--year", "2026"])
    assert code == 0 and out_json["ok"]
    assert out_json["files"] == 1
    manifest = json.loads((out / "MANIFEST.json").read_text())
    assert manifest["file_count"] == 1
    assert manifest["files"][0]["sha256"]


def test_verify_passes(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "inv.xml").write_text("<x/>")
    out = tmp_path / "out"
    run(["--source", str(src), "--output", str(out), "--year", "2026"])
    code, out_json = run(["--source", str(src), "--output", str(out),
                          "--year", "2026", "--verify"])
    assert code == 0 and out_json["verify"]["ok"]


def test_empty_source(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out"
    code, out_json = run(["--source", str(src), "--output", str(out), "--year", "2026"])
    assert code == 0 and out_json["files"] == 0


def test_missing_source_errors(tmp_path):
    code, out_json = run(["--source", str(tmp_path / "nope"),
                          "--output", str(tmp_path / "out"), "--year", "2026"])
    assert code == 2 and "not a directory" in out_json["error"]
