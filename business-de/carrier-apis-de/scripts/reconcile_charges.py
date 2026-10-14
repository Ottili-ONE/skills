#!/usr/bin/env python3
"""Match carrier charge lines to Ottili ledger entries by reference.

A charge with no ledger entry is an ``unknown_result`` — it is NOT an error,
it is a reconciliation gap that a human must close. Exits non-zero while any
row is unknown so the caller cannot silently close a period.

Usage:
    python3 reconcile_charges.py --charges charges.csv --ledger ledger.json
Exit 0 = every charge matched. Exit 1 = unknown rows remain.
"""
import argparse
import csv
import json
import sys
from pathlib import Path


def load_ledger(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {r["reference"]: r for r in data}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--charges", required=True, help="carrier charge CSV")
    ap.add_argument("--ledger", required=True, help="Ottili ledger JSON")
    args = ap.parse_args()

    ledger = load_ledger(Path(args.ledger))
    unknown = []
    matched = 0
    with Path(args.charges).open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            ref = row.get("reference") or row.get("clientReferenceNo")
            if ref in ledger:
                matched += 1
            else:
                unknown.append({"reference": ref, "amount": row.get("amount")})
    print(json.dumps({"matched": matched, "unknown": unknown}, indent=2))
    return 1 if unknown else 0


if __name__ == "__main__":
    sys.exit(main())
