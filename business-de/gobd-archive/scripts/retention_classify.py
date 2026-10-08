#!/usr/bin/env python3
"""Assign a GoBD retention class and end date to an accounting document.

Usage:
    python3 retention_classify.py --type invoice --year 2026
    python3 retention_classify.py --type annual-account --year 2024
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

# BEG IV / AO §147 Abs. 3 n.F. (effective 2025-01-01). Verified 2026-10-08.
CLASSES = {
    "invoice": ("Buchungsbeleg", 8),
    "voucher": ("Buchungsbeleg", 8),
    "bank-statement": ("Buchungsbeleg", 8),
    "booking": ("Buchungsbeleg", 8),
    "ledger": ("Bücher / Jahresabschluss", 10),
    "annual-account": ("Bücher / Jahresabschluss", 10),
    "balance-sheet": ("Bücher / Jahresabschluss", 10),
    "correspondence": ("Geschäftskorrespondenz", 6),
    "contract": ("Geschäftskorrespondenz", 6),
}


def retention_end(year: int, years: int) -> str:
    return f"{year + years}-12-31"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--type", required=True,
                    choices=sorted(CLASSES), type=str.lower)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    pinned = load_config(args.config)["gobd-archive"]
    label, years = CLASSES[args.type]
    end = retention_end(args.year, years)
    print(json.dumps({
        "document_type": args.type,
        "retention_class": label,
        "retention_years": years,
        "effective_date": pinned["ao147"]["effective"],
        "retention_end": end,
        "purge_permitted_after": end,
        "note": "Deletion requires a documented purge decision with an approval "
                "record; the purge record itself is kept for the full retention.",
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
