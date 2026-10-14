#!/usr/bin/env python3
"""Validate a bank reconciliation.

Reads a JSON reconciliation:
  {account, opening, closing, entries:[...], open_items:[...]}
Checks: balance equation, duplicate detection, allocation completeness,
reason-code coverage and the EUR 0.01 rounding boundary.
Exits 0 on success, 2 on failure.

Edge cases handled:
  - opening + entries != closing -> hard stop
  - duplicate (same amount, reference, value date) -> blocked
  - entry marked matched with no open item -> rejected
  - unallocated entry without a reason_code -> rejected
  - difference exactly at the EUR 0.01 boundary -> needs a reason code
  - a matched entry whose amount has no open item at all -> rejected
"""
import json
import sys
from pathlib import Path

ROUNDING_TOLERANCE = 0.01
VALID_REASON_CODES = {"ROUNDING", "BANK_FEE", "FX", "UNALLOCATED"}


def german_iban_ok(iban: str) -> bool:
    """Bundesbank Pruefzahlenberechnung for DE IBANs.

    German check digits are NOT generic mod-97: the country code and check
    digits move to the END of the string before the mod-97 step, and letters
    are converted to numbers (A=10..Z=35). A valid DE IBAN yields remainder 1.
    """
    s = str(iban).replace(" ", "").upper()
    if len(s) != 22 or not s.startswith("DE") or not s[2:].isdigit():
        return False
    rearranged = s[4:] + s[:4]
    nums = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
    return int(nums) % 97 == 1


def check(data):
    errors = []
    entries = data.get("entries", [])
    opening = float(data.get("opening", 0.0))
    closing = float(data.get("closing", 0.0))
    open_items = data.get("open_items", [])

    expected = round(opening + sum(float(e.get("amount", 0.0)) for e in entries), 2)
    if abs(expected - closing) > ROUNDING_TOLERANCE:
        errors.append(f"balance mismatch: opening+entries={expected:.2f} != closing={closing:.2f}")

    seen = set()
    for i, e in enumerate(entries, 1):
        amt = round(float(e.get("amount", 0.0)), 2)
        ref = str(e.get("reference", "")).strip()
        vdate = str(e.get("date", "")).strip()
        key = (amt, ref, vdate)
        if key in seen:
            errors.append(f"entry {i}: duplicate {key} — block allocation and escalate to the bank")
        seen.add(key)

        matched = e.get("matched")
        reason = str(e.get("reason_code", "")).strip()
        if matched and not e.get("open_item_id"):
            errors.append(f"entry {i}: marked matched but no open_item_id — cannot allocate")
        if matched and e.get("open_item_id") and e.get("open_item_id") not in {str(o.get("id", "")) for o in open_items}:
            errors.append(f"entry {i}: open_item_id {e.get('open_item_id')!r} not in open_items")
        if not matched and not reason:
            errors.append(f"entry {i}: unallocated without a reason_code")
        if reason and reason not in VALID_REASON_CODES:
            errors.append(f"entry {i}: unknown reason_code {reason!r} (expected one of {sorted(VALID_REASON_CODES)})")

    # Difference analysis: every entry that is not matched to an open item
    # must carry a reason code, and the total unallocated amount must be
    # explainable (either rounding-scale or a declared reason code).
    unmatched_total = round(sum(
        float(e.get("amount", 0.0)) for e in entries if not e.get("matched")
    ), 2)
    if abs(unmatched_total) >= ROUNDING_TOLERANCE:
        if not any(str(e.get("reason_code", "")).strip() for e in entries if not e.get("matched")):
            errors.append(
                f"unallocated total {unmatched_total:.2f} >= {ROUNDING_TOLERANCE:.2f} "
                "and no reason_code declared"
            )
    return errors


def main(argv):
    """Entry point. argv is sys.argv[1:].

    Positional: <recon.json>. Optional: --no-iban (skip the IBAN check; the
    legacy fixtures use a placeholder account and the IBAN check is
    exercised separately by evals_fixtures/iban_invalid.json).
    """
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: recon_check.py <recon.json> [--no-iban]", file=sys.stderr)
        print("       --no-iban  skip the IBAN check (test fixtures only)",
              file=sys.stderr)
        return 2
    path = argv[0]
    no_iban = "--no-iban" in argv[1:]
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print("FAIL", e, file=sys.stderr)
        return 2
    iban_bad = False
    if not no_iban and data.get("account") and not german_iban_ok(str(data["account"])):
        print(f"FAIL IBAN {data['account']!r} invalid "
              f"(Bundesbank Pruefzahlenberechnung)", file=sys.stderr)
        iban_bad = True
    errs = check(data)
    if errs:
        for e in errs:
            print("FAIL", e, file=sys.stderr)
        return 2
    if iban_bad:
        return 2
    print("OK reconciliation valid, %d entries" % len(data.get("entries", [])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
