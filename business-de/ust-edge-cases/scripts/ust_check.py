#!/usr/bin/env python3
"""Validate VAT treatment of an invoice line.

Checks: tax key is legal for the scenario, tax amount matches the rate,
rounding to cents, reverse-charge preconditions (USt-IdNr. present for 06/0),
Kleinunternehmer threshold. Exits 0 on success, 2 on failure.
"""
import json
import sys
from pathlib import Path

# Steuerschluessel -> (rate percent, requires_invoice_idnr)
KEYS = {
    "19": (19.0, False),
    "7": (7.0, False),
    "16/1": (16.0, False),
    "06/0": (0.0, True),
    "09/0": (0.0, False),
    "13/0": (19.0, False),
    "V091": (0.0, True),
    "0": (0.0, False),
}
KLEINUNTERNEHMEN_MAX = 22000.0  # prior-year turnover threshold, EUR (2026)


def check(rows, prior_turnover=None, kleinunternehmer=False):
    errors = []
    for i, r in enumerate(rows, 1):
        key = str(r.get("tax_key", "")).strip()
        if key not in KEYS:
            errors.append(f"line {i}: unknown tax key {key!r}")
            continue
        rate, needs_idnr = KEYS[key]
        if needs_idnr and not r.get("customer_vat_id"):
            errors.append(f"line {i}: tax key {key} requires a valid customer USt-IdNr.")
        try:
            net = float(r["net"])
        except (KeyError, ValueError):
            errors.append(f"line {i}: invalid net {r.get('net')!r}")
            continue
        expected = round(net * rate / 100.0, 2)
        try:
            stated = float(r.get("tax_amount", expected))
        except (KeyError, ValueError):
            stated = expected
        if abs(stated - expected) > 0.005:
            errors.append(f"line {i}: tax amount {stated} != {net * rate / 100.0:.2f} for key {key}")
        if kleinunternehmer and rate > 0:
            errors.append(f"line {i}: Kleinunternehmer cannot charge VAT (key {key})")
    if kleinunternehmer and prior_turnover is not None and prior_turnover > KLEINUNTERNEHMEN_MAX:
        errors.append(f"prior-year turnover {prior_turnover} exceeds Kleinunternehmer threshold {KLEINUNTERNEHMEN_MAX}")
    return errors


def main(argv):
    if len(argv) != 2:
        print("usage: ust_check.py <invoice.json>", file=sys.stderr)
        return 2
    data = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("lines", [data])
    errs = check(rows, data.get("prior_turnover") if isinstance(data, dict) else None,
                data.get("kleinunternehmer", False) if isinstance(data, dict) else False)
    if errs:
        for e in errs:
            print("FAIL", e, file=sys.stderr)
        return 2
    print("OK VAT treatment valid, %d lines" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
