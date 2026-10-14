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


# --- hardened audit behaviour (added in EXPAND pass) ---

def test_audit_flags_clamping(tmp_path: Path) -> None:
    src = FIXTURE.read_text(encoding="utf-8")
    bad = tmp_path / "clamping_driver.py"
    bad.write_text(src.replace(
        "    def left_click(self, input_data):\n        self._scale(input_data)",
        "    def left_click(self, input_data):\n        x, y = self._scale(input_data)\n"
        "        x = max(0, min(x, 1280))\n        y = max(0, min(y, 720))\n",
    ), encoding="utf-8")
    r = run(str(bad))
    assert r.returncode == 1
    assert "clamp" in r.stderr.lower()


def test_audit_flags_missing_scaling(tmp_path: Path) -> None:
    """A driver with pointer methods that never scale is unsafe."""
    src = FIXTURE.read_text(encoding="utf-8")
    bad = tmp_path / "noscale_driver.py"
    # remove every _scale call and input.copy() reference
    # also strip the comment that mentions input.copy(), so no scaling signal survives
    bad.write_text(src.replace("self._scale(input_data)", "pass")
                   .replace("return input.copy()", "return input")
                   .replace("input.copy() is the signal", "scaled into a fresh array"),
                   encoding="utf-8")
    r = run(str(bad))
    assert r.returncode == 1
    assert "scale" in r.stderr.lower()


def test_audit_json_mode() -> None:
    r = run(str(FIXTURE), "--json")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["mode"] == "audit"
    assert data["valid"] is True


def test_contract_json_mode() -> None:
    r = run("--contract", str(REGISTRY), "--json")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["mode"] == "contract"
    assert data["valid"] is True
    assert data["fails"] == 0


def test_contract_empty_members_fails(tmp_path: Path) -> None:
    reg = tmp_path / "empty.json"
    reg.write_text(json.dumps({"members": []}), encoding="utf-8")
    r = run("--contract", str(reg))
    assert r.returncode == 1
    assert "empty" in r.stderr.lower()


def test_contract_invalid_json_fails(tmp_path: Path) -> None:
    reg = tmp_path / "bad.json"
    reg.write_text("not json", encoding="utf-8")
    r = run("--contract", str(reg))
    assert r.returncode == 2


# --- reference coverage (added in EXPAND pass) ---

def test_reference_files_exist_and_are_substantive():
    refs = ROOT / "references"
    for name in ("tree-protocol.md", "safety-layers.md", "coordinate-scaling.md"):
        p = refs / name
        assert p.is_file(), f"missing reference {name}"
        assert len(p.read_text(encoding="utf-8").splitlines()) >= 25, f"{name} too thin"


# --- hardened audit edge cases (EXPAND pass 2) ---

def test_audit_rejects_empty_file(tmp_path: Path) -> None:
    p = tmp_path / "empty.py"
    p.write_text("", encoding="utf-8")
    r = run(str(p))
    assert r.returncode == 1
    assert "empty" in r.stderr.lower()


def test_audit_rejects_non_text_file(tmp_path: Path) -> None:
    p = tmp_path / "binary.py"
    p.write_bytes(b"\x89PNG\r\n\x1a\n\x00" * 8)
    r = run(str(p))
    assert r.returncode == 1
    assert "not readable text" in r.stderr


def test_contract_drift_16_members(tmp_path: Path) -> None:
    """The real near-miss: the published registry has 17 members; a 16-member
    clone is the drift trap."""
    members = [m for m in ("screenshot", "zoom", "cursor_position", "mouse_move",
        "left_mouse_down", "left_mouse_up", "left_click", "left_click_drag",
        "right_click", "middle_click", "double_click", "triple_click", "scroll",
        "wait", "type", "key", "hold_key") if m != "triple_click"]
    reg = tmp_path / "drift.json"
    reg.write_text(json.dumps({"members": members}), encoding="utf-8")
    r = run("--contract", str(reg))
    assert r.returncode == 1
    assert "drift" in r.stderr.lower()
    assert "triple_click" in r.stderr


def test_contract_accepts_canonical_registry() -> None:
    r = run("--contract", str(ROOT / "fixtures" / "registry_20260801.json"),
            "--json")
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["valid"] is True
    assert out["mode"] == "contract"
    assert out["fails"] == 0


# --- tree-as-gate (EXPAND pass 2) ---

def test_tree_gate_present():
    """The fixture driver enumerates the tree and exposes a usability gate."""
    r = run(str(FIXTURE))
    assert r.returncode == 0, r.stderr
    assert "0 0" in r.stdout


def test_tree_without_gate_fails(tmp_path: Path) -> None:
    src = FIXTURE.read_text(encoding="utf-8")
    bad = tmp_path / "no_gate.py"
    bad.write_text(src.replace(
        "    def tree_is_usable(self):",
        "    def tree_is_missing(self):",
    ), encoding="utf-8")
    r = run(str(bad))
    assert r.returncode == 1
    assert "tree_is_usable" in r.stderr


def test_tree_fallback_to_pixels_fails(tmp_path: Path) -> None:
    src = FIXTURE.read_text(encoding="utf-8")
    bad = tmp_path / "fallback.py"
    bad.write_text(src + "\n    def click(self, x, y):\n"
                      "        if not self.tree_is_usable():\n"
                      "            return self._pixel_click(x, y)  # fallback to pixels\n",
                 encoding="utf-8")
    r = run(str(bad))
    assert r.returncode == 1
    assert "fallback" in r.stderr.lower()
