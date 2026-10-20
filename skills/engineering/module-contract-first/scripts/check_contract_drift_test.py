#!/usr/bin/env python3
"""Self-tests for check_contract_drift.py (SKL-W0-01 TASK-0003 repair).

The self-test runs in both CI shapes:

    pytest -q skills/engineering/module-contract-first/scripts/check_contract_drift_test.py
    python3 skills/engineering/module-contract-first/scripts/check_contract_drift_test.py

Every path is derived from this file's own location, so the self-test works in
any checkout (a fresh clone included) and never writes outside the temporary
directory it creates for the test at hand.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
CHECKER_MODULE = "scripts.check_contract_drift"


def run_checker(*args: str) -> subprocess.CompletedProcess:
    """Run the checker as a module, from the skill directory that owns it."""
    return subprocess.run(
        [sys.executable, "-m", CHECKER_MODULE, *args],
        capture_output=True,
        text=True,
        cwd=str(SKILL_DIR),
    )


def make_module(tmp: Path) -> Path:
    """Create a throwaway module with a public surface and a contract folder."""
    mod = tmp / "mymod"
    mod.mkdir(parents=True, exist_ok=True)
    (mod / "__init__.py").write_text("def hello(): pass\nclass Greeter: pass\n")
    (mod / "module-contracts").mkdir(exist_ok=True)
    return mod


def snapshot_path(mod: Path) -> Path:
    return mod / "module-contracts" / "mymod.json"


def test_enumerate_creates_snapshot(tmp_path: Path) -> None:
    """--enumerate writes a snapshot that holds the public symbols."""
    mod = make_module(tmp_path)
    snap = snapshot_path(mod)
    r = run_checker("--enumerate", str(mod))
    assert r.returncode == 0, f"enumerate failed: {r.stderr}"
    assert snap.is_file(), f"snapshot not created at {snap}"
    data = json.loads(snap.read_text())
    assert "hello" in data["symbols"], f"hello not in symbols: {data}"
    assert "Greeter" in data["symbols"], f"Greeter not in symbols: {data}"


def test_check_passes_when_live_matches_snapshot(tmp_path: Path) -> None:
    """--check is green while the live surface still matches the snapshot."""
    mod = make_module(tmp_path)
    r = run_checker("--enumerate", str(mod))
    assert r.returncode == 0, f"enumerate failed: {r.stderr}"
    r = run_checker("--check", str(mod))
    assert r.returncode == 0, f"check failed on matching snapshot: {r.stderr}"


def test_check_detects_drift_and_passes_after_update(tmp_path: Path) -> None:
    """A new export is drift; re-enumerating (never hand-editing) clears it."""
    mod = make_module(tmp_path)
    r = run_checker("--enumerate", str(mod))
    assert r.returncode == 0, f"enumerate failed: {r.stderr}"
    (mod / "new_func.py").write_text("def new_func(): pass\n")
    r = run_checker("--check", str(mod))
    assert r.returncode == 1, f"check should fail on drift: {r.stdout}{r.stderr}"
    assert "DRIFT DETECTED" in (r.stdout + r.stderr), (
        f"check should report drift: {r.stdout}{r.stderr}"
    )
    r2 = run_checker("--enumerate", str(mod))
    assert r2.returncode == 0, f"enumerate failed: {r2.stderr}"
    data = json.loads(snapshot_path(mod).read_text())
    assert data["symbols"] == sorted(set(data["symbols"])), (
        f"snapshot has duplicates: {data}"
    )
    r3 = run_checker("--check", str(mod))
    assert r3.returncode == 0, f"check should pass after snapshot update: {r3.stderr}"


def test_cycles_command_runs(tmp_path: Path) -> None:
    """--cycles analyses the import graph and returns a verdict (0 = clean)."""
    mod = make_module(tmp_path)
    r = run_checker("--cycles", str(mod))
    assert r.returncode in (0, 1), f"cycles command crashed: {r.stdout}{r.stderr}"


TESTS = (
    test_enumerate_creates_snapshot,
    test_check_passes_when_live_matches_snapshot,
    test_check_detects_drift_and_passes_after_update,
    test_cycles_command_runs,
)


def main() -> int:
    """Standalone runner: every check gets its own temporary module."""
    failures = 0
    for test in TESTS:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                test(Path(tmp))
            except AssertionError as exc:
                print(f"FAIL {test.__name__}: {exc}")
                failures += 1
            else:
                print(f"ok   {test.__name__}")
    print(f"check_contract_drift self-test: {'PASS' if failures == 0 else 'FAIL'}")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
