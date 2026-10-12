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
