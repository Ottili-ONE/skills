"""Tests for scripts/verify_harness.py (offline, deterministic)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_harness.py"
FIX = ROOT / "tests" / "fixtures"


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
    # With the two live checks the lazy agent writes output.json but no
    # summary.md, so it scores 1/2 = 0.50 and power vs lazy is 0.50. Asking
    # for 0.51 must fail; the boundary value 0.50 itself passes.
    r = run(
        "--checks", str(FIX / "checks.json"),
        "--contract", str(FIX / "contract.json"),
        "--good", str(FIX / "good"),
        "--broken", str(FIX / "broken"),
        "--lazy", str(FIX / "lazy"),
        "--min-power", "0.51",
    )
    assert r.returncode == 1
    assert "does not separate good from lazy" in r.stderr


def test_boundary_min_power_passes() -> None:
    # power vs lazy is exactly 0.50 with the shipped fixtures; requesting the
    # boundary value must pass (>= comparison, not >).
    r = run(
        "--checks", str(FIX / "checks.json"),
        "--contract", str(FIX / "contract.json"),
        "--good", str(FIX / "good"),
        "--broken", str(FIX / "broken"),
        "--lazy", str(FIX / "lazy"),
        "--min-power", "0.5",
    )
    assert r.returncode == 0, r.stderr
    assert "PASS: harness discriminates" in r.stderr


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
    assert "lack a valid spec reference" in r.stderr


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


def test_bypass_audit_passes_on_generated_register() -> None:
    r = run(
        "--bypass-audit", str(FIX / "SPEC.json"), str(FIX / "bypass-register.jsonl"),
        "--checks", str(FIX / "checks.json"),
        "--contract", str(FIX / "contract.json"),
        "--good", str(FIX / "good"),
        "--broken", str(FIX / "broken"),
        "--lazy", str(FIX / "lazy"),
    )
    assert r.returncode == 0, r.stderr
    assert "PASS: every check has a bypass-register entry with >= 2 defences" in r.stderr


def test_bypass_audit_fails_when_register_is_empty() -> None:
    empty = FIX / "bypass-empty.jsonl"
    empty.write_text("")
    r = run(
        "--bypass-audit", str(FIX / "SPEC.json"), str(empty),
        "--checks", str(FIX / "checks.json"),
        "--contract", str(FIX / "contract.json"),
        "--good", str(FIX / "good"),
        "--broken", str(FIX / "broken"),
        "--lazy", str(FIX / "lazy"),
    )
    assert r.returncode == 1
    assert "no bypass-register entry" in r.stderr


def test_bypass_audit_fails_on_single_defence() -> None:
    one = FIX / "bypass-one-defence.jsonl"
    one.write_text(json.dumps({
        "check": "output_file_exists", "severity": "low",
        "direct": "x", "indirect": "y", "cosmetic": "z",
        "defences": ["output_file.exists"],
    }) + "\n")
    r = run(
        "--bypass-audit", str(FIX / "SPEC.json"), str(one),
        "--checks", str(FIX / "checks.json"),
        "--contract", str(FIX / "contract.json"),
        "--good", str(FIX / "good"),
        "--broken", str(FIX / "broken"),
        "--lazy", str(FIX / "lazy"),
    )
    assert r.returncode == 1
    assert "rule of two needs >= 2" in r.stderr
