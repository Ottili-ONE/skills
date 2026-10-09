#!/usr/bin/env python3
"""Verify that an eval harness discriminates good, broken and lazy agents.

Reads a sandbox contract and per-agent output directories, runs the checks
defined in the contract, computes pass rates and reports discriminating power.
Exits 0 only when the harness separates a known-good agent from both a broken
and a lazy agent by at least MIN_POWER (default 0.30).

Fully offline and deterministic: no network, no wall-clock, fixed seed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MIN_POWER = 0.30
MIN_GOOD_PASS_RATE = 0.80
DEFAULT_CONTRACT = {
    "network": "deny",
    "filesystem": "scoped",
    "exec": "allowlisted",
    "time_seconds": 300,
    "secrets": "none",
}


def load_contract(path: Path | None) -> dict:
    if path is None:
        return dict(DEFAULT_CONTRACT)
    data = json.loads(path.read_text(encoding="utf-8"))
    contract = dict(DEFAULT_CONTRACT)
    contract.update(data)
    return contract


def assert_contract(contract: dict) -> list[str]:
    """Return a list of FAIL lines; empty means the sandbox is pinned."""
    failures: list[str] = []
    if contract.get("network") != "deny":
        failures.append("FAIL: sandbox network policy is not 'deny'")
    if contract.get("filesystem") != "scoped":
        failures.append("FAIL: sandbox filesystem is not 'scoped'")
    if contract.get("exec") not in ("allowlisted", "none"):
        failures.append("FAIL: sandbox exec policy is not allowlisted/none")
    if not isinstance(contract.get("time_seconds"), int) or not (1 <= contract["time_seconds"] <= 3600):
        failures.append("FAIL: sandbox time_seconds is not a bounded int in [1,3600]")
    if contract.get("secrets") not in ("none", "redacted"):
        failures.append("FAIL: sandbox secrets policy is not none/redacted")
    return failures


def load_checks(checks_path: Path) -> list[dict]:
    data = json.loads(checks_path.read_text(encoding="utf-8"))
    checks = data.get("checks", data) if isinstance(data, dict) else data
    if not isinstance(checks, list):
        raise ValueError("checks file must contain a JSON list of check objects")
    return checks


def assert_checks_spec_ref(checks: list[dict], spec_path: Path | None) -> list[str]:
    """Every check must reference a line in the spec it was derived from."""
    failures: list[str] = []
    if spec_path is None:
        return failures
    spec_text = spec_path.read_text(encoding="utf-8")
    for c in checks:
        ref = c.get("spec_ref")
        if not ref:
            failures.append(f"FAIL: check '{c.get('name', 'unnamed')}' has no spec_ref")
            continue
        if ref not in spec_text:
            failures.append(
                f"FAIL: check '{c.get('name', 'unnamed')}' spec_ref '{ref}' not found in {spec_path.name}"
            )
    return failures


def assert_checks_bypass_register(checks: list[dict], register_path: Path | None) -> list[str]:
    """Every check must have a written bypass entry in the register."""
    failures: list[str] = []
    if register_path is None:
        return failures
    text = register_path.read_text(encoding="utf-8")
    for c in checks:
        name = c.get("name", "unnamed")
        if f"### {name}" not in text:
            failures.append(f"FAIL: check '{name}' has no bypass-register entry")
    return failures


def run_checks(checks: list[dict], agent_dir: Path) -> tuple[int, int, list[str]]:
    """Return (passed, total, detail_lines)."""
    passed = 0
    total = len(checks)
    details: list[str] = []
    for c in checks:
        name = c.get("name", "unnamed")
        path = agent_dir / c["path"]
        if c.get("exists", True):
            ok = path.is_file()
        else:
            ok = not path.is_file()
        if ok and "content_equals" in c:
            ok = path.read_text(encoding="utf-8").strip() == c["content_equals"].strip()
        if ok and "json_field" in c:
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
                ok = obj.get(c["json_field"]) == c["json_value"]
            except (json.JSONDecodeError, OSError):
                ok = False
        passed += 1 if ok else 0
        details.append(f"{'PASS' if ok else 'FAIL'}: {name} ({c['path']})")
    return passed, total, details


def pass_rate(passed: int, total: int) -> float:
    if total == 0:
        return 0.0
    return passed / total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contract", type=Path, default=None, help="sandbox contract JSON")
    ap.add_argument("--checks", type=Path, required=True, help="spec-derived checks JSON")
    ap.add_argument("--good", type=Path, required=True, help="known-good agent output dir")
    ap.add_argument("--broken", type=Path, required=True, help="deliberately broken agent output dir")
    ap.add_argument("--lazy", type=Path, required=True, help="deliberately lazy agent output dir")
    ap.add_argument("--min-power", type=float, default=MIN_POWER)
    ap.add_argument("--min-good-pass-rate", type=float, default=MIN_GOOD_PASS_RATE,
                    help="known-good agent must pass at least this fraction")
    ap.add_argument("--spec", type=Path, default=None,
                    help="spec markdown; every check must carry a spec_ref found in it")
    ap.add_argument("--bypass-register", type=Path, default=None,
                    help="bypass register markdown; every check must have an entry")
    ap.add_argument("--json", type=Path, default=None, help="write machine-readable report here")
    args = ap.parse_args()

    contract = load_contract(args.contract)
    contract_failures = assert_contract(contract)
    for line in contract_failures:
        print(line, file=sys.stderr)

    checks = load_checks(args.checks)
    spec_failures = assert_checks_spec_ref(checks, args.spec)
    for line in spec_failures:
        print(line, file=sys.stderr)
    register_failures = assert_checks_bypass_register(checks, args.bypass_register)
    for line in register_failures:
        print(line, file=sys.stderr)

    report: dict = {"contract": contract, "contract_ok": not contract_failures,
                    "spec_ok": not spec_failures, "bypass_register_ok": not register_failures,
                    "checks": len(checks), "agents": {}}

    for label, d in (("good", args.good), ("broken", args.broken), ("lazy", args.lazy)):
        passed, total, details = run_checks(checks, d)
        rate = pass_rate(passed, total)
        report["agents"][label] = {"passed": passed, "total": total, "pass_rate": rate}
        print(f"INFO: {label} agent {passed}/{total} = {rate:.0%}", file=sys.stderr)
        for line in details:
            print(f"  {line}", file=sys.stderr)

    good = report["agents"]["good"]["pass_rate"]
    broken = report["agents"]["broken"]["pass_rate"]
    lazy = report["agents"]["lazy"]["pass_rate"]
    power_vs_broken = good - broken
    power_vs_lazy = good - lazy
    report["power_vs_broken"] = power_vs_broken
    report["power_vs_lazy"] = power_vs_lazy
    report["min_power"] = args.min_power

    good_ok = good >= args.min_good_pass_rate
    report["good_pass_rate"] = good
    report["min_good_pass_rate"] = args.min_good_pass_rate
    report["good_ok"] = good_ok
    ok = (contract_failures == [] and spec_failures == [] and register_failures == []
          and power_vs_broken >= args.min_power and power_vs_lazy >= args.min_power
          and good_ok)
    report["ok"] = ok
    print(f"INFO: discriminating power vs broken = {power_vs_broken:.2f}, vs lazy = {power_vs_lazy:.2f} (min {args.min_power})", file=sys.stderr)

    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if not ok:
        if contract_failures:
            print("FAIL: sandbox contract is not pinned", file=sys.stderr)
        if spec_failures:
            print(f"FAIL: {len(spec_failures)} check(s) lack a valid spec reference", file=sys.stderr)
        if register_failures:
            print(f"FAIL: {len(register_failures)} check(s) have no bypass-register entry", file=sys.stderr)
        if power_vs_broken < args.min_power:
            print(f"FAIL: harness does not separate good from broken (power {power_vs_broken:.2f} < {args.min_power})", file=sys.stderr)
        if power_vs_lazy < args.min_power:
            print(f"FAIL: harness does not separate good from lazy (power {power_vs_lazy:.2f} < {args.min_power})", file=sys.stderr)
        if not good_ok:
            print(f"FAIL: known-good agent passes only {good:.0%} (min {args.min_good_pass_rate:.0%}) — checks are too strict", file=sys.stderr)
        return 1
    print("PASS: harness discriminates good, broken and lazy agents", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
