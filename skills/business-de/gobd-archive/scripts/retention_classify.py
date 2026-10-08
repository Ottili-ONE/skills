#!/usr/bin/env python3
"""Assign a GoBD retention class and end date to an accounting document.

Usage:
    python3 retention_classify.py --type invoice --year 2026
    python3 retention_classify.py --type annual-account --year 2024 --json
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
    """Retention runs from the end of the calendar year of creation."""
    return f"{year + years}-12-31"


def classify(doc_type: str, year: int, config: dict) -> dict:
    """Return the full classification record. Raises ValueError on bad input."""
    if doc_type not in CLASSES:
        raise ValueError(f"unknown document type: {doc_type!r}; "
                         f"choose from {sorted(CLASSES)}")
    if not isinstance(year, int) or year < 1900 or year > 2100:
        raise ValueError(f"implausible invoice year: {year!r}")
    label, years = CLASSES[doc_type]
    pinned = config["gobd-archive"]
    end = retention_end(year, years)
    return {
        "document_type": doc_type,
        "retention_class": label,
        "retention_years": years,
        "effective_date": pinned["ao147"]["effective"],
        "retention_end": end,
        "purge_permitted_after": end,
        "deletion_requires": [
            "documented purge decision",
            "approval record from the tax advisor / management",
            "the purge record itself kept for the full retention period",
        ],
        "note": ("Deletion before the retention end is never permitted. "
                 "After the end, delete only via a documented, auditable purge."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--type", required=True, type=str.lower)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--config", default="config/versions.json")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON")
    args = ap.parse_args()

    try:
        pinned = load_config(args.config)
        rec = classify(args.type, args.year, pinned)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2,
                         ensure_ascii=False), file=sys.stderr)
        return 2

    if args.json:
        rec = {"ok": True, **rec}
        print(json.dumps(rec, indent=2, ensure_ascii=False))
    else:
        print(f"{rec['document_type']} -> {rec['retention_class']} "
              f"({rec['retention_years']}y), retention end {rec['retention_end']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
