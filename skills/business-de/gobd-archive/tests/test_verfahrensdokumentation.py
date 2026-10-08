"""Tests for verfahrensdokumentation.py: build + self-check."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "verfahrensdokumentation.py"
CONFIG = Path(__file__).resolve().parent.parent.parent.parent / "business-de" / "config" / "versions.json"


def run(args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args, "--config", str(CONFIG)],
                       capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout or r.stderr)


def test_build_emits_all_sections(tmp_path):
    out = tmp_path / "vd.json"
    code, doc = run(["--system", "ERP v5.2", "--out", str(out)])
    assert code == 0
    sections = doc["verfahrensdokumentation"]["sections"]
    assert set(sections) == {"system", "medium", "retention", "export", "access", "backup"}
    assert sections["system"]["complete"] is True
    assert sections["medium"]["complete"] is False  # empty by default
    assert out.exists()


def test_check_passes_when_complete(tmp_path):
    out = tmp_path / "vd.json"
    run(["--system", "ERP v5.2", "--medium", "S3", "--out", str(out)])
    code, res = run(["--check", str(out)])
    assert code == 0 and res["ok"]
    assert res["missing_sections"] == []


def test_check_flags_missing(tmp_path):
    out = tmp_path / "vd.json"
    run(["--system", "ERP v5.2", "--out", str(out)])
    code, res = run(["--check", str(out)])
    assert code == 1
    assert "medium" in res["missing_sections"]
