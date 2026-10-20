#!/usr/bin/env python3
"""Decide PASS or FAIL from the output of the RLS leak-test probe.

The probe runs as the application role and prints one line per measurement:

    a_sees_own<TAB>1
    a_sees_b<TAB>0

``a_sees_own`` is the number of rows tenant A may see (it seeded exactly one),
``a_sees_b`` is the number of rows of tenant B that tenant A may see. A leak
test passes when the first number is 1 and the second is 0.

A measurement that is missing is a failure, not a zero: the probe did not run,
and a probe that did not run proves nothing.

Usage: check_leak_probe.py <probe-output-file>
Exit 0 = PASS, 1 = FAIL, 2 = usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MEASUREMENT_RE = re.compile(r"^(?P<name>[a-z_]+)\t(?P<value>\d+)\s*$")
ERROR_RE = re.compile(r"^\s*(?:psql:.*)?\s*ERROR:", re.IGNORECASE)


def read_measurements(text: str) -> tuple[dict[str, int], list[str]]:
    """Return the measurements of a probe output and the error lines it holds."""
    measurements: dict[str, int] = {}
    errors: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if ERROR_RE.match(line):
            errors.append(line)
            continue
        match = MEASUREMENT_RE.match(line)
        if match:
            measurements[match.group("name")] = int(match.group("value"))
    return measurements, errors


def judge(text: str) -> tuple[bool, list[str]]:
    """Return (passed, findings) for a probe output."""
    measurements, errors = read_measurements(text)
    findings: list[str] = []
    for error in errors:
        findings.append(f"probe error: {error}")
    own = measurements.get("a_sees_own")
    cross = measurements.get("a_sees_b")
    if own is None:
        findings.append("probe did not report a_sees_own (the probe did not run)")
    elif own != 1:
        findings.append(f"same-tenant read wrong (expected 1, got {own})")
    if cross is None:
        findings.append("probe did not report a_sees_b (the probe did not run)")
    elif cross != 0:
        findings.append(f"cross-tenant leak (expected 0, got {cross})")
    return (not findings), findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("output", help="file with the captured probe output")
    args = ap.parse_args()

    path = Path(args.output)
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        print(f"FAIL: cannot read the probe output {path}: {exc}", file=sys.stderr)
        return 2

    passed, findings = judge(text)
    if passed:
        print("PASS: RLS leak test green")
        return 0
    print(f"FAIL: RLS leak test - block merge ({path})", file=sys.stderr)
    for finding in findings:
        print(f"  - {finding}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
