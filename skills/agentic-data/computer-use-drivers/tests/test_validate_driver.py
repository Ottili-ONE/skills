"""Tests for scripts/validate_driver.py (offline, deterministic)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_driver.py"
FIXTURE = ROOT / "fixtures" / "sample_driver.py"
# Vendored copy of the published registry, fetched live 2026-10-12.
# The test stays fully offline; re-vendor on every SDK release.
REGISTRY = ROOT / "fixtures" / "registry_20260801.json"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True,
    )


def test_contract_matches_published_registry() -> None:
    """The 17-member set must match the live computer_toolset_20260801.json."""
    assert REGISTRY.is_file(), "registry fixture missing — re-vendor on SDK release"
    r = run("--contract", str(REGISTRY))
    assert r.returncode == 0, r.stderr
    assert "1 0 0" in r.stdout


def test_fixture_driver_passes_audit() -> None:
    r = run(str(FIXTURE))
    assert r.returncode == 0, r.stderr
    assert "0 0" in r.stdout


def test_driver_missing_member_fails(tmp_path: Path) -> None:
    src = FIXTURE.read_text(encoding="utf-8")
    bad = tmp_path / "bad_driver.py"
    bad.write_text(src.replace("    def screenshot(self, input_data):\n", ""),
                   encoding="utf-8")
    r = run(str(bad))
    assert r.returncode == 1
    assert "screenshot" in r.stderr


def test_ungated_member_not_gated(tmp_path: Path) -> None:
    """A mouse_* method must NOT call confirm()."""
    src = FIXTURE.read_text(encoding="utf-8")
    bad = tmp_path / "overgated_driver.py"
    bad.write_text(src.replace(
        "    def left_click(self, input_data):\n        self._scale(input_data)",
        "    def left_click(self, input_data):\n        self.confirm('left_click', input_data)\n        self._scale(input_data)",
    ), encoding="utf-8")
    r = run(str(bad))
    assert r.returncode == 1
    assert "left_click" in r.stderr and "confirm" in r.stderr


def test_gated_member_calls_confirm(tmp_path: Path) -> None:
    """A type method MUST call confirm(); stripping it is a safety failure."""
    src = FIXTURE.read_text(encoding="utf-8")
    bad = tmp_path / "ungated_type.py"
    bad.write_text(src.replace(
        "    def type(self, input_data):\n        if not self.confirm(\"type\", input_data):\n            raise ToolsetUsageError(\"declined\")\n        return \"typed\"",
        "    def type(self, input_data):\n        return \"typed\"",
    ), encoding="utf-8")
    r = run(str(bad))
    assert r.returncode == 1
    assert "type" in r.stderr and "confirm" in r.stderr


def test_contract_drift_detected(tmp_path: Path) -> None:
    reg = tmp_path / "drift.json"
    reg.write_text(json.dumps({
        "type": "computer_toolset_20260801",
        "toolset_name": "computer",
        "members": ["screenshot", "zoom", "cursor_position"],
        "default_disabled": [],
    }), encoding="utf-8")
    r = run("--contract", str(reg))
    assert r.returncode == 1
    assert "drift" in r.stderr


def test_contract_unknown_member_warns(tmp_path: Path) -> None:
    members = ["key", "hold_key", "type", "cursor_position", "mouse_move",
               "left_mouse_down", "left_mouse_up", "left_click", "left_click_drag",
               "right_click", "middle_click", "double_click", "triple_click",
               "scroll", "wait", "screenshot", "zoom", "bogus_member"]
    reg = tmp_path / "extra.json"
    reg.write_text(json.dumps({
        "type": "computer_toolset_20260801",
        "toolset_name": "computer",
        "members": members,
        "default_disabled": [],
    }), encoding="utf-8")
    r = run("--contract", str(reg))
    assert r.returncode == 1
    assert "bogus_member" in r.stderr


def test_contract_non_list_members_fails(tmp_path: Path) -> None:
    reg = tmp_path / "bad.json"
    reg.write_text(json.dumps({"members": "not-a-list"}), encoding="utf-8")
    r = run("--contract", str(reg))
    assert r.returncode == 1
    assert "members" in r.stderr.lower()


def test_missing_file_returns_2() -> None:
    r = run("/no/such/driver.py")
    assert r.returncode == 2
