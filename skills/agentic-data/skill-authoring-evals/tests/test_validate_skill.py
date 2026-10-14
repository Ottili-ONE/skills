"""Tests for scripts/validate_skill.py (offline, deterministic)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_skill.py"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True,
    )


def test_valid_skill_passes() -> None:
    r = run(str(ROOT.parent / "mcp-2026-07-28"))
    assert r.returncode == 0, r.stderr
    assert "0 0" in r.stdout


def test_missing_dir_fails_with_exit_2() -> None:
    r = run("/no/such/dir/here")
    assert r.returncode == 2
    assert "not found" in r.stderr


def test_json_report_written() -> None:
    out = ROOT / "report_test.json"
    out.unlink(missing_ok=True)
    r = run(str(ROOT.parent / "mcp-2026-07-28"), "--json", str(out))
    assert r.returncode == 0
    data = json.loads(out.read_text())
    assert data["ok"] is True
    assert data["skill"] == "mcp-2026-07-28"


def test_json_parent_missing_fails() -> None:
    r = run(str(ROOT.parent / "mcp-2026-07-28"),
            "--json", "/no/such/dir/report.json")
    assert r.returncode == 2


# --- reference-link resolution (added in PASS 3 / TEST+FIX) ---

def test_dangling_reference_link_is_hard_fail(tmp_path: Path) -> None:
    skill = tmp_path / "dangling-skill"
    (skill / "references").mkdir(parents=True)
    (skill / "references" / "real.md").write_text("ok", encoding="utf-8")
    (skill / "SKILL.md").write_text(
        "---\nname: dangling-skill\ndescription: x\n---\n"
        "see references/real.md and references/missing.md\n",
        encoding="utf-8",
    )
    r = run(str(skill))
    assert r.returncode == 1
    assert "missing.md" in r.stderr


def test_reference_link_escape_is_hard_fail(tmp_path: Path) -> None:
    skill = tmp_path / "escape-skill"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: escape-skill\ndescription: x\n---\n"
        "see references/../escape.md\n",
        encoding="utf-8",
    )
    r = run(str(skill))
    assert r.returncode == 1
    assert "escape" in r.stderr


def test_valid_skill_reports_ok() -> None:
    r = run(str(ROOT.parent / "mcp-2026-07-28"))
    assert r.returncode == 0
    assert "0 0" in r.stdout


# --- evals_check.py (EXPAND pass 2) ---

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _run(script, *args, input=None):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        input=input, capture_output=True, text=True)


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


GOOD = json.dumps([
    {"id": "E1", "prompt": "My skill folder is `my-skill` but the frontmatter says `name: other`. What happens?", "should_fire": True, "expected_output": "The skill never registers."},
    {"id": "N1", "prompt": "Write a README for my new Python package.", "should_fire": False, "expected_output": "Not a skill-authoring task."},
])


def test_evals_check_accepts_good(tmp_path):
    p = _write(tmp_path, "good.json", GOOD)
    r = _run("evals_check.py", p)
    assert r.returncode == 0, r.stderr
    assert "2 0 0" in r.stdout


def test_evals_check_rejects_missing_expected_output(tmp_path):
    bad = json.dumps([{"id": "E1", "prompt": "x", "should_fire": True}])
    p = _write(tmp_path, "bad.json", bad)
    r = _run("evals_check.py", p)
    assert r.returncode == 1
    assert "expected_output" in r.stderr


def test_evals_check_rejects_duplicate_id(tmp_path):
    bad = json.dumps([
        {"id": "E1", "prompt": "a", "should_fire": True, "expected_output": "x"},
        {"id": "E1", "prompt": "b", "should_fire": False, "expected_output": "y"},
    ])
    p = _write(tmp_path, "dup.json", bad)
    r = _run("evals_check.py", p)
    assert r.returncode == 1
    assert "duplicate" in r.stderr.lower()


def test_evals_check_warns_on_no_negatives(tmp_path):
    only_pos = json.dumps([
        {"id": "E1", "prompt": "a", "should_fire": True, "expected_output": "x"},
        {"id": "E2", "prompt": "b", "should_fire": True, "expected_output": "y"},
    ])
    p = _write(tmp_path, "pos.json", only_pos)
    r = _run("evals_check.py", p)
    assert r.returncode == 0
    assert "should-not-fire" in r.stderr


def test_evals_check_json_mode(tmp_path):
    p = _write(tmp_path, "good.json", GOOD)
    r = _run("evals_check.py", p, "--json")
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["valid"] is True
    assert out["cases"] == 2
    assert out["should_fire"] == 1
    assert out["should_not_fire"] == 1


def test_evals_check_rejects_empty_file(tmp_path):
    p = _write(tmp_path, "empty.json", "")
    r = _run("evals_check.py", p)
    assert r.returncode == 2
    assert "empty" in r.stderr.lower()


def test_evals_check_rejects_non_list(tmp_path):
    p = _write(tmp_path, "obj.json", json.dumps({"not": "a list"}))
    r = _run("evals_check.py", p)
    assert r.returncode == 2
    assert "list" in r.stderr.lower()
