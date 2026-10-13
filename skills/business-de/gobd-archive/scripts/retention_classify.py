#!/usr/bin/env python3
"""Assign a GoBD retention class and end date to an accounting document.

The 6-year class (Geschäftskorrespondenz) is narrower than "all correspondence":
per whk-controlling.de (re-fetched 2026-10-13) it covers exactly three
sub-types, listed in CORRESPONDENCE_SUBTYPES below. A draft, a working file, or
a deleted chat message that no system can reproduce is NOT a valid substitute.

Usage:
    python3 retention_classify.py --type invoice --year 2026
    python3 retention_classify.py --type correspondence --year 2026 --json
    python3 retention_classify.py --type correspondence --year 2026 --subtype incoming-letter
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _classes import classify, CLASSES  # noqa: E402

# The three sub-types of the 6-year class. Verified 2026-10-13 against
# whk-controlling.de (last modified 2026-04-14). Anything outside this list is
# NOT Geschäftskorrespondenz — classify it as a voucher (8y) or a book (10y)
# instead, or ask the tax advisor.
CORRESPONDENCE_SUBTYPES = {
    "incoming-letter": "empfangene Handels- oder Geschäftsbriefe",
    "outgoing-letter-copy": "Wiedergabe der abgesandten Handelsbriefe",
    "tax-relevant": "sonstige Unterlagen mit steuerlicher Bedeutung",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--type", required=True, type=str.lower)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--subtype", default=None,
                    choices=sorted(CORRESPONDENCE_SUBTYPES),
                    help="only meaningful for --type correspondence")
    ap.add_argument("--config", default="config/versions.json")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON")
    args = ap.parse_args()

    try:
        label, years, end = classify(args.type, args.year)
    except ValueError as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2,
                         ensure_ascii=False), file=sys.stderr)
        return 2

    rec = {
        "document_type": args.type,
        "retention_class": label,
        "retention_years": years,
        "retention_end": end,
        "purge_permitted_after": end,
    }
    if args.type == "correspondence":
        if args.subtype is None:
            rec["warning"] = (
                "the 6-year class covers only three sub-types; without a "
                "--subtype the classification is unconfirmed. Pass one of "
                f"{sorted(CORRESPONDENCE_SUBTYPES)} or ask the tax advisor.")
            rec["subtypes"] = CORRESPONDENCE_SUBTYPES
        else:
            rec["subtype"] = args.subtype
            rec["subtype_meaning"] = CORRESPONDENCE_SUBTYPES[args.subtype]

    if args.json:
        print(json.dumps({"ok": True, **rec}, indent=2, ensure_ascii=False))
    else:
        print(f"{rec['document_type']} -> {rec['retention_class']} "
              f"({rec['retention_years']}y), retention end {rec['retention_end']}")
        if rec.get("warning"):
            print(f"WARNING: {rec['warning']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
