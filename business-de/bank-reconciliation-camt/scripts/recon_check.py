#!/usr/bin/env python3
"""Validate a bank reconciliation.

Reads a JSON reconciliation: {account, opening, closing, entries:[...], open_items:[...]}.
Checks: balance equation, duplicate detection, allocation completeness.
Exits 0 on success, 2 on failure.
"""
import json
import sys
from pathlib import Path

ROUNDING_TOLERANCE = 0.01


def check(data):
    errors = []
    entries = data.get("entries", [])
    opening = float(data.get("opening", 0.0))
    closing = float(data.get("closing", 0.0))
    expected = round(opening + sum(float(e.get("amount", 0.0)) for e in entries), 2)
    if abs(expected - closing) > ROUNDING_TOLERANCE:
        errors.append(f"balance mismatch: opening+entries={expected:.2f} != closing={closing:.2f}")

    seen = set()
    for i, e in enumerate(entries, 1):
        key = (round(float(e.get("amount", 0.0)), 2), str(e.get("reference", "")).strip(),
               str(e.get("date", "")).strip())
        if key in seen:
            errors.append(f"entry {i}: duplicate {key}")
        seen.add(key)
        if not e.get("matched") and not e.get("reason_code"):
            errors.append(f"entry {i}: unallocated without a reason_code")
    return errors


def main(argv):
    if len(argv) != 2:
        print("usage: recon_check.py <recon.json>", file=sys.stderr)
        return 2
    data = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    errs = check(data)
    if errs:
        for e in errs:
            print("FAIL", e, file=sys.stderr)
        return 2
    print("OK reconciliation valid, %d entries" % len(data.get("entries", [])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
