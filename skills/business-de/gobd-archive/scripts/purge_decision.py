#!/usr/bin/env python3
"""Record a GoBD-compliant purge decision for documents whose retention ended.

A deletion is only permitted after the retention end date AND only via a
documented, auditable purge with an approval record. The purge record itself
must be kept for the full retention period (AO §147 / BEG IV, effective
2025-01-01, verified 2026-10-13 via dejure.org).

TWO independent blockers must BOTH be cleared:

| Blocker | Cleared when | Checked by |
|---|---|---|
| retention end reached | today is after `retention_end` (year + N, 12-31) | `retention_end_reached` |
| no open audit | no audit is currently in progress | `no_open_audit` |

This script exits non-zero while either blocker stands, so it is safe to wire
into a CI gate.

Usage:
    python3 purge_decision.py --type invoice --year 2017 \
        --approver "M. Mustermann (Steuerberater)" \
        --reason "Retention 2025-12-31 elapsed, no open audit" \
        --out purge-2017.json
    python3 purge_decision.py --type invoice --year 2026 --open-audit
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _classes import classify  # noqa: E402


def decide(doc_type: str, year: int, approver: str, reason: str,
           open_audit: bool = False, today: date = None) -> dict:
    """Return the purge decision record. Raises ValueError on bad input."""
    if today is None:
        today = date.today()
    if not approver or not approver.strip():
        raise ValueError("approver must be a non-empty name")
    if not reason or not reason.strip():
        raise ValueError("reason must be a non-empty justification")
    label, years, end = classify(doc_type, year)
    end_date = date.fromisoformat(end)
    end_reached = today > end_date
    permitted = end_reached and not open_audit
    blockers = []
    if not end_reached:
        blockers.append("retention_end_not_reached")
    if open_audit:
        blockers.append("audit_open")
    return {
        "document_type": doc_type,
        "retention_class": label,
        "retention_years": years,
        "document_year": year,
        "retention_end": end,
        "decision_date": today.isoformat(),
        "purge_permitted": permitted,
        "blocking_conditions": {
            "retention_end_reached": end_reached,
            "no_open_audit": not open_audit,
        },
        "blockers": blockers,
        "approver": approver.strip(),
        "reason": reason.strip(),
        # The purge record is itself a document: keep it for the full retention
        # period of the documents it describes (a 2017 voucher purge record is
        # kept until 2025-12-31, NOT until today + years).
        "record_retention_until": end,
        "record_retention_note": (
            "This record is a document in its own right. Retain it until the "
            "retention end of the documents it describes, i.e. "
            f"{end} — not until {today.isoformat()} plus {years} years."),
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
    ap.add_argument("--today", default=None,
                    help="decision date YYYY-MM-DD (default: today; pin for "
                         "deterministic runs and CI)")
    ap.add_argument("--config", default="config/versions.json")
    ap.add_argument("--out", help="write the decision record as JSON")
    args = ap.parse_args()

    today = None
    if args.today:
        try:
            today = date.fromisoformat(args.today)
        except ValueError:
            print(json.dumps({"ok": False,
                              "error": f"bad --today value: {args.today!r} "
                                       "(expected YYYY-MM-DD)"},
                             indent=2, ensure_ascii=False), file=sys.stderr)
            return 2

    try:
        rec = decide(args.type, args.year, args.approver, args.reason,
                     args.open_audit, today)
    except ValueError as e:
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
