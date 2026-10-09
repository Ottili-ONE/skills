"""Tests for scripts/verify_harness.py (offline, deterministic)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_harness.py"
FIX = Path("/srv/ottili/repo/skills/../../scratch/skills/skills-agentic-data-r3/verif_fixtures")


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True,
    )


def test_help() -> None:
    r = run("--help")
    assert r.returncode == 0
    assert "sandbox" in r.stdout.lower() or "contract" in r.stdout.lower()


def test_good_separates_from_broken_and_lazy() -> None:
    r = run(
        "--checks", str(FIX / "checks.json"),
        "--contract", str(FIX / "contract.json"),
        "--good", str(FIX / "good"),
        "--broken", str(FIX / "broken"),
        "--lazy", str(FIX / "lazy"),
    )
    assert r.returncode == 0, r.stderr
    assert "PASS: harness discriminates" in r.stderr


def test_broken_contract_fails() -> None:
    r = run(
        "--checks", str(FIX / "checks.json"),
        "--contract", str(FIX / "contract_broken.json"),
        "--good", str(FIX / "good"),
        "--broken", str(FIX / "broken"),
        "--lazy", str(FIX / "lazy"),
    )
    assert r.returncode == 1
    assert "network policy is not 'deny'" in r.stderr


def test_low_min_power_fails() -> None:
    # good=1.0, lazy=0.67 -> power 0.33; requesting 0.5 must fail.
    r = run(
        "--checks", str(FIX / "checks.json"),
        "--contract", str(FIX / "contract.json"),
        "--good", str(FIX / "good"),
        "--broken", str(FIX / "broken"),
        "--lazy", str(FIX / "lazy"),
        "--min-power", "0.5",
    )
    assert r.returncode == 1
    assert "vs lazy" in r.stderr


def test_json_report_written() -> None:
    out = FIX / "report_test.json"
    out.unlink(missing_ok=True)
    r = run(
        "--checks", str(FIX / "checks.json"),
        "--contract", str(FIX / "contract.json"),
        "--good", str(FIX / "good"),
        "--broken", str(FIX / "broken"),
        "--lazy", str(FIX / "lazy"),
        "--json", str(out),
    )
    assert r.returncode == 0
    data = json.loads(out.read_text())
    assert data["ok"] is True
    assert data["agents"]["good"]["pass_rate"] == 1.0
    assert data["agents"]["broken"]["pass_rate"] < 1.0


def test_spec_ref_missing_fails() -> None:
    bad = FIX / "checks_noref.json"
    bad.write_text(json.dumps({"checks": [
        {"name": "x", "path": "output.json", "exists": True}]}))
    r = run(
        "--checks", str(bad),
        "--contract", str(FIX / "contract.json"),
        "--spec", str(FIX / "SPEC.md"),
        "--good", str(FIX / "good"),
        "--broken", str(FIX / "broken"),
        "--lazy", str(FIX / "lazy"),
    )
    assert r.returncode == 1
    assert "spec_ref" in r.stderr


def test_bypass_register_missing_fails() -> None:
    r = run(
        "--checks", str(FIX / "checks.json"),
        "--contract", str(FIX / "contract.json"),
        "--bypass-register", str(FIX / "SPEC.md"),
        "--good", str(FIX / "good"),
        "--broken", str(FIX / "broken"),
        "--lazy", str(FIX / "lazy"),
    )
    assert r.returncode == 1
    assert "bypass-register entry" in r.stderr


def test_full_pipeline_with_spec_and_register() -> None:
    r = run(
        "--checks", str(FIX / "checks.json"),
        "--contract", str(FIX / "contract.json"),
        "--spec", str(FIX / "SPEC.md"),
        "--bypass-register", str(ROOT / "references" / "bypass-register.md"),
        "--good", str(FIX / "good"),
        "--broken", str(FIX / "broken"),
        "--lazy", str(FIX / "lazy"),
    )
    assert r.returncode == 0, r.stderr
    assert "PASS: harness discriminates" in r.stderr
