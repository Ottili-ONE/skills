"""Tests for scripts/bon_cap.py — best-of-N jailbreak attempt cap.

Offline and deterministic: every test gets its own state file.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bon_cap.py"


def run(state: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--task", "t1", "--state", str(state), *args],
        capture_output=True, text=True,
    )


def test_under_cap_passes(tmp_path: Path) -> None:
    st = tmp_path / "cap.json"
    for _ in range(10):
        r = run(st, "--attempt", "click")
        assert r.returncode == 0, r.stderr
        assert "PASS" in r.stderr


def test_task_cap_hit(tmp_path: Path) -> None:
    st = tmp_path / "cap.json"
    for i in range(50):
        r = run(st, "--attempt", "click")
        if i < 49:
            assert r.returncode == 0, r.stderr
    # the 51st attempt (count 51 > 50) must hit the cap
    r = run(st, "--attempt", "click")
    assert r.returncode == 1
    assert "cap hit" in r.stderr
    assert "51/50" in r.stderr


def test_check_reports_status(tmp_path: Path) -> None:
    st = tmp_path / "cap.json"
    run(st, "--attempt", "click")
    r = run(st, "--check")
    assert r.returncode == 0
    assert "1/50" in r.stderr


def test_check_when_cap_hit(tmp_path: Path) -> None:
    st = tmp_path / "cap.json"
    # 50 attempts fill the task budget; the 51st is the one that hits the cap.
    for _ in range(50):
        run(st, "--attempt", "click")
    r = run(st, "--attempt", "click")
    assert r.returncode == 1
    assert "cap hit" in r.stderr
    r = run(st, "--check")
    assert r.returncode == 1
    assert "cap hit" in r.stderr


def test_reset_clears_counters(tmp_path: Path) -> None:
    st = tmp_path / "cap.json"
    for _ in range(50):
        run(st, "--attempt", "click")
    r = run(st, "--reset")
    assert r.returncode == 0
    r = run(st, "--check")
    assert r.returncode == 0
    assert "0/50" in r.stderr


def test_missing_state_file_is_allowed(tmp_path: Path) -> None:
    st = tmp_path / "absent.json"
    r = run(st, "--check")
    assert r.returncode == 0
    assert "0/50" in r.stderr


def test_bad_state_file_fails(tmp_path: Path) -> None:
    st = tmp_path / "bad.json"
    st.write_text("not json", encoding="utf-8")
    r = run(st, "--check")
    assert r.returncode == 2
    assert "unreadable" in r.stderr
