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
    try:
        data = json.loads(checks_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"ERROR: checks file is not valid JSON: {e}")
    checks = data.get("checks", data) if isinstance(data, dict) else data
    if not isinstance(checks, list):
        raise SystemExit("ERROR: checks file must contain a JSON list of check objects")
    if not checks:
        raise SystemExit("ERROR: checks file is empty")
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


def assert_check_defences(checks: list[dict]) -> list[str]:
    """Every check needs at least two independent defences (rule of two).

    A check with exactly one defence is a single point of failure: the agent
    either does the intended work or finds the one unintended path. Defence
    families are: existence, content equality, JSON field, word count, and
    the sandbox contract. A check that asserts only existence has one defence
    and is flagged here so it can be given a second one before shipping.
    """
    failures: list[str] = []
    for c in checks:
        defences = 0
        if c.get("exists", True):
            defences += 1
        if "content_equals" in c:
            defences += 1
        if "json_field" in c:
            defences += 1
        if "min_words" in c or "max_words" in c:
            defences += 1
        if "keywords" in c:
            defences += 1
        if defences < 2:
            failures.append(
                f"FAIL: check '{c.get('name', 'unnamed')}' has {defences} defence(s); "
                f"the rule of two requires >= 2 independent defences"
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
        if ok and "min_words" in c:
            words = len(path.read_text(encoding="utf-8").split())
            ok = words >= int(c["min_words"])
            details.append(f"INFO: {name} word_count={words} min={c['min_words']}")
        if ok and "max_words" in c:
            words = len(path.read_text(encoding="utf-8").split())
            ok = words <= int(c["max_words"])
        if ok and "keywords" in c:
            text = path.read_text(encoding="utf-8").lower()
            hits = [k for k in c["keywords"] if k.lower() in text]
            ok = len(hits) >= int(c.get("min_keywords", 1))
            details.append(f"INFO: {name} keyword_hits={len(hits)} need>={c.get('min_keywords', 1)}")
        passed += 1 if ok else 0
        details.append(f"{'PASS' if ok else 'FAIL'}: {name} ({c['path']})")
    return passed, total, details


def pass_rate(passed: int, total: int) -> float:
    if total == 0:
        return 0.0
    return passed / total


def _die(msg: str, code: int = 2) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return code


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contract", type=Path, default=None, help="sandbox contract JSON")
    ap.add_argument("--checks", type=Path, required=True, help="spec-derived checks JSON")
    ap.add_argument("--good", type=Path, required=True, help="known-good agent output dir")
    ap.add_argument("--broken", type=Path, required=True, help="deliberately broken agent output dir")
    ap.add_argument("--lazy", type=Path, required=True, help="deliberately lazy agent output dir")
    ap.add_argument("--spec", type=Path, default=None, help="spec markdown (for spec_ref validation)")
    ap.add_argument("--bypass-register", type=Path, default=None, help="bypass register markdown")
    ap.add_argument("--min-power", type=float, default=MIN_POWER)
    ap.add_argument("--min-good-pass-rate", type=float, default=MIN_GOOD_PASS_RATE)
    ap.add_argument("--json", type=Path, default=None, help="write JSON report here")
    ap.add_argument("--bypass-audit", nargs=2, metavar=("SPEC", "REGISTER"), default=None,
                    help="audit the bypass register against the spec checks (every check needs a register entry with >= 2 defences and no critical severity)")
    ap.add_argument("--neutered-checks", type=Path, default=None,
                    help="verify the verifier: checks with one flipped to always-pass. The power must drop vs the live run and this command must exit 1.")
    args = ap.parse_args()

    for name in ("checks",):
        if not args.checks.is_file():
            return _die(f"checks file not found: {args.checks}")
    for name in ("good", "broken", "lazy"):
        d = getattr(args, name)
        if not d.is_dir():
            return _die(f"{name} dir not found: {d}")
    if args.spec and not args.spec.is_file():
        return _die(f"--spec file not found: {args.spec}")
    if args.bypass_register and not args.bypass_register.is_file():
        return _die(f"--bypass-register file not found: {args.bypass_register}")
    if args.bypass_audit:
        spec_p, reg_p = args.bypass_audit
        if not Path(spec_p).is_file():
            return _die(f"--bypass-audit spec file not found: {spec_p}")
        if not Path(reg_p).is_file():
            return _die(f"--bypass-audit register file not found: {reg_p}")
    if args.json and not args.json.parent.is_dir():
        return _die(f"--json parent dir missing: {args.json.parent}")
    for opt, val in (("--min-power", args.min_power),
                     ("--min-good-pass-rate", args.min_good_pass_rate)):
        if not (0.0 <= val <= 1.0):
            return _die(f"{opt}={val} must be in [0, 1]")

    try:
        checks = load_checks(args.checks)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 2

    if args.bypass_audit:
        spec_p, reg_p = args.bypass_audit
        try:
            spec_obj = json.loads(Path(spec_p).read_text(encoding="utf-8"))
            register_rows = load_bypass_register(reg_p)
        except SystemExit as e:
            print(str(e), file=sys.stderr)
            return 2
        bypass_failures = audit_bypass_register(register_rows, spec_obj.get("checks", []))
        rule_of_two_failures = assert_check_defences(spec_obj.get("checks", []))
        for f in bypass_failures + rule_of_two_failures:
            print(f, file=sys.stderr)
        if bypass_failures or rule_of_two_failures:
            print(
                f"FAIL: {len(bypass_failures) + len(rule_of_two_failures)} "
                f"bypass-register problem(s)",
                file=sys.stderr,
            )
            return 1
        print("PASS: every check has a bypass-register entry with >= 2 defences", file=sys.stderr)

    contract = load_contract(args.contract)
    contract_failures = assert_contract(contract)
    spec_failures = assert_checks_spec_ref(checks, args.spec)
    register_failures = assert_checks_bypass_register(checks, args.bypass_register)

    good_passed, total, _ = run_checks(checks, args.good)
    broken_passed, _, _ = run_checks(checks, args.broken)
    lazy_passed, _, _ = run_checks(checks, args.lazy)

    good = pass_rate(good_passed, total)
    broken = pass_rate(broken_passed, total)
    lazy = pass_rate(lazy_passed, total)

    power_vs_broken = good - broken
    power_vs_lazy = good - lazy
    good_ok = good >= args.min_good_pass_rate

    ok = (
        not contract_failures
        and not spec_failures
        and not register_failures
        and power_vs_broken >= args.min_power
        and power_vs_lazy >= args.min_power
        and good_ok
    )

    detail: list[str] = []
    for cf in contract_failures:
        detail.append(f"FAIL: {cf}")
    if contract_failures:
        detail.append("FAIL: sandbox contract is not pinned")
    if spec_failures:
        detail.append(f"FAIL: {len(spec_failures)} check(s) lack a valid spec reference")
    if register_failures:
        detail.append(f"FAIL: {len(register_failures)} check(s) have no bypass-register entry")
    if power_vs_broken < args.min_power:
        detail.append(f"FAIL: harness does not separate good from broken (power {power_vs_broken:.2f} < {args.min_power})")
    if power_vs_lazy < args.min_power:
        detail.append(f"FAIL: harness does not separate good from lazy (power {power_vs_lazy:.2f} < {args.min_power})")
    if not good_ok:
        detail.append(f"FAIL: known-good agent passes only {good:.0%} (min {args.min_good_pass_rate:.0%}) — checks are too strict")

    report = {
        "ok": ok,
        "contract": contract,
        "n_checks": total,
        "agents": {
            "good": {"pass_rate": round(good, 4), "passed": good_passed},
            "broken": {"pass_rate": round(broken, 4), "passed": broken_passed},
            "lazy": {"pass_rate": round(lazy, 4), "passed": lazy_passed},
        },
        "power": {
            "vs_broken": round(power_vs_broken, 4),
            "vs_lazy": round(power_vs_lazy, 4),
            "min_power": args.min_power,
        },
        "good_pass_rate_min": args.min_good_pass_rate,
        "failures": detail,
    }

    print(
        f"INFO: good={good:.2f} broken={broken:.2f} lazy={lazy:.2f} "
        f"power(broken)={power_vs_broken:.2f} power(lazy)={power_vs_lazy:.2f}",
        file=sys.stderr,
    )
    for d in detail:
        print(d, file=sys.stderr)

    if args.neutered_checks is not None:
        if not args.neutered_checks.is_file():
            return _die(f"neutered checks file not found: {args.neutered_checks}")
        try:
            neutered = load_checks(args.neutered_checks)
        except SystemExit as e:
            print(str(e), file=sys.stderr)
            return 2
        if len(neutered) != total:
            detail.append(f"FAIL: neutered checks have {len(neutered)} checks, expected {total}")
        else:
            ng, _, _ = run_checks(neutered, args.good)
            nl, _, _ = run_checks(neutered, args.lazy)
            nb, _, _ = run_checks(neutered, args.broken)
            n_power_lazy = pass_rate(ng, total) - pass_rate(nl, total)
            n_power_broken = pass_rate(ng, total) - pass_rate(nb, total)
            report["neutered"] = {
                "power_vs_lazy": round(n_power_lazy, 4),
                "power_vs_broken": round(n_power_broken, 4),
            }
            if n_power_lazy >= power_vs_lazy or n_power_broken >= power_vs_broken:
                detail.append(
                    f"FAIL: neutering a check did not drop power "
                    f"(lazy {n_power_lazy:.2f} vs {power_vs_lazy:.2f}, "
                    f"broken {n_power_broken:.2f} vs {power_vs_broken:.2f}); "
                    "the verifier is not verified")
            else:
                print("INFO: neutering a check dropped power; verifier verified",
                      file=sys.stderr)

    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if not ok:
        return 1
    if any("FAIL: neutering" in d for d in detail):
        return 1
    print("PASS: harness discriminates good, broken and lazy agents", file=sys.stderr)
    return 0


def load_bypass_register(path: str) -> list[dict]:
    """Load the bypass register. Each row: {check, direct, indirect, cosmetic, severity, defences}."""
    p = Path(path)
    if not p.is_file():
        raise SystemExit(f"ERROR: bypass register not found: {path}")
    rows: list[dict] = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            print(f"FAIL: bypass register line {i} is not valid JSON: {exc}", file=sys.stderr)
            raise SystemExit(1)
    return rows


def audit_bypass_register(rows: list[dict], checks: list[dict]) -> list[str]:
    """Audit the bypass register against the spec checks.

    Returns a list of failure strings (empty = PASS). Enforces:
    - every check has at least one register entry (no un-audited check),
    - no entry carries a critical (direct) severity,
    - every check has >= 2 independent defences (rule of two).
    """
    failures: list[str] = []
    for c in checks:
        cid = c.get("id") or c.get("name", "?")
        entries = [r for r in rows if r.get("check") == cid]
        if not entries:
            failures.append(f"FAIL: check {cid} has no bypass-register entry")
            continue
        severities = {str(r.get("severity", "low")).lower() for r in entries}
        if "critical" in severities:
            failures.append(f"FAIL: check {cid} has a critical (direct) bypass")
        defences: list[str] = []
        for r in entries:
            for d in r.get("defences", []):
                if d not in defences:
                    defences.append(d)
        if len(defences) < 2:
            failures.append(
                f"FAIL: check {cid} has {len(defences)} defence(s); rule of two needs >= 2"
            )
    return failures


def cmd_bypass(args: argparse.Namespace) -> int:
    """Audit the bypass register against the checks in the spec."""
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    checks = spec.get("checks", [])
    rows = load_bypass_register(args.bypass)
    failures = audit_bypass_register(rows, checks)
    print(
        f"INFO: bypass register: {len(rows)} entries for {len(checks)} checks, "
        f"{len(failures)} problem(s)",
        file=sys.stderr,
    )
    for f in failures:
        print(f, file=sys.stderr)
    if failures:
        print(f"FAIL: {len(failures)} bypass-register problem(s)", file=sys.stderr)
        return 1
    print("PASS: every check has a bypass-register entry with >= 2 defences", file=sys.stderr)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())


