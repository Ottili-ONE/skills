#!/usr/bin/env python3
"""Record a GoBD-compliant purge decision for documents whose retention ended.

A deletion is only permitted after the retention end date AND only via a
documented, auditable purge with an approval record. The purge record itself
must be kept for the full retention period (AO §147 / BEG IV, effective
2025-01-01, verified 2026-10-09).

Usage:
    python3 purge_decision.py --type invoice --year 2017 --approver "M. Mustermann (Steuerberater)" --reason "Retention 2025-12-31 elapsed, no open audit" --out purge-2017.json
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

CLASSES = {  # BEG IV / AO §147 Abs. 3 n.F., verified 2026-10-09
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


def decide(doc_type: str, year: int, approver: str, reason: str,
           open_audit: bool = False, config: dict = None) -> dict:
    if doc_type not in CLASSES:
        raise ValueError(f"unknown document type: {doc_type!r}; "
                         f"choose from {sorted(CLASSES)}")
    if not isinstance(year, int) or year < 1900 or year > 2100:
        raise ValueError(f"implausible year: {year!r}")
    if not approver or not approver.strip():
        raise ValueError("approver must be a non-empty name")
    if not reason or not reason.strip():
        raise ValueError("reason must be a non-empty justification")
    label, years = CLASSES[doc_type]
    end = retention_end(year, years)
    today = date.today()
    permitted = (today > date.fromisoformat(end)) and not open_audit
    return {
        "document_type": doc_type,
        "retention_class": label,
        "retention_years": years,
        "document_year": year,
        "retention_end": end,
        "decision_date": today.isoformat(),
        "purge_permitted": permitted,
        "blocking_conditions": {
            "retention_end_reached": today > date.fromisoformat(end),
            "no_open_audit": not open_audit,
        },
        "approver": approver.strip(),
        "reason": reason.strip(),
        "record_retention_until": retention_end(today.year, years),
        "note": ("Deletion before the retention end is never permitted. "
                 "After the end, delete only via this documented, auditable "
                 "purge. Keep this record for the full retention period."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--type", required=True, type=str.lower)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--approver", required=True)
    ap.add_argument("--reason", required=True)
    ap.add_argument("--open-audit", action="store_true",
                    help="an audit is currently open -> purge blocked")
    ap.add_argument("--config", default="config/versions.json")
    ap.add_argument("--out", help="write the decision record as JSON")
    args = ap.parse_args()

    try:
        config = load_config(args.config)
        rec = decide(args.type, args.year, args.approver, args.reason,
                     args.open_audit, config)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2,
                         ensure_ascii=False), file=sys.stderr)
        return 2

    if args.out:
        Path(args.out).write_text(
            json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    print(json.dumps(rec, indent=2, ensure_ascii=False))
    return 0 if rec["purge_permitted"] else 1


if __name__ == "__main__":
    sys.exit(main())
