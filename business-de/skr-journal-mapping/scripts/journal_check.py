#!/usr/bin/env python3
"""Validate a SKR03/SKR04 journal (Buchungsstapel) for balance and tax-key sanity.

Reads a JSON journal (list of posting lines) or a CSV with columns
account, side (S/H), amount, tax_key, ref. Exits 0 on success, 2 on failure.
"""
import csv
import json
import sys
from pathlib import Path

VALID_SIDES = {"S", "H"}
VALID_TAX_KEYS = {"19", "7", "16/1", "16", "1", "06/0", "09/0", "13/0", "0", "00"}


def load_rows(path: Path):
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("["):
        return json.loads(text)
    rows = []
    with path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    return rows


def check(rows):
    errors = []
    debit = 0.0
    credit = 0.0
    for i, r in enumerate(rows, 1):
        side = (r.get("side") or "").strip().upper()
        if side not in VALID_SIDES:
            errors.append(f"line {i}: invalid side {side!r}")
            continue
        try:
            amt = float(r["amount"])
        except (KeyError, ValueError):
            errors.append(f"line {i}: invalid amount {r.get('amount')!r}")
            continue
        if side == "S":
            debit += amt
        else:
            credit += amt
        tk = (r.get("tax_key") or "").strip()
        if tk and tk not in VALID_TAX_KEYS:
            errors.append(f"line {i}: unknown tax key {tk!r}")
    if abs(debit - credit) > 0.005:
        errors.append(f"journal does not balance: debit={debit:.2f} credit={credit:.2f}")
    return errors


def main(argv):
    if len(argv) != 2:
        print("usage: journal_check.py <journal.json|journal.csv>", file=sys.stderr)
        return 2
    rows = load_rows(Path(argv[1]))
    errs = check(rows)
    if errs:
        for e in errs:
            print("FAIL", e, file=sys.stderr)
        return 2
    print("OK journal balanced, %d lines" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
