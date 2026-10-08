#!/usr/bin/env python3
"""Build a DATEV EXTF Buchungsstapel CSV from a list of booking lines.

Usage:
    python3 build_stapel.py --berater 29098 --mandant 55003 --wj-start 20260101 \
        --from 20260601 --to 20260630 --label "Shop 06/2026" --skr 03 \
        --booking 1200,S,4000,19,RE2026-114,Netto 19% \
        --booking 500,S,4200,7,RE2026-115,Netto 7% \
        --booking 100,S,8000,0,RE2026-116,Netto 0% \
        --output stapel.csv
"""
import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

DELIMITER = ";"
HEADER_FIELDS = 31
BOOKING_COLUMNS = 125
FORMAT_VERSION = "13"
CATEGORY = "21"
FORMAT_NAME = "Buchungsstapel"


def build_header(args, pinned):
    today = date.today().strftime("%Y%m%d")
    row = [""] * HEADER_FIELDS
    row[0] = "EXTF"
    row[1] = pinned["extf_schema"]["version"].split("/")[0]
    row[2] = CATEGORY
    row[3] = FORMAT_NAME
    row[4] = FORMAT_VERSION
    row[5] = today
    row[7] = args.absender or ""
    row[8] = args.exported_by or ""
    row[9] = args.imported_by or ""
    row[10] = args.berater
    row[11] = args.mandant
    row[12] = args.wj_start
    row[13] = str(args.skl)
    row[14] = args.from_date
    row[15] = args.to_date
    row[16] = args.label
    row[17] = args.diktat or ""
    row[20] = "1"  # Festschreibung
    row[21] = args.wkz or "EUR"
    row[26] = args.skr or ""
    row[30] = args.info or ""
    return row


def build_booking(parts):
    if len(parts) < 6:
        raise SystemExit("booking must be amount,side,account,taxkey,beleg,text")
    amount, side, account, taxkey, beleg, text = parts[:6]
    row = [""] * BOOKING_COLUMNS
    row[0] = amount.replace(".", ",")   # col 1 Umsatz
    row[1] = side                        # col 2 Soll/Haben
    row[6] = account                     # col 7 Konto
    row[9] = beleg                       # col 10 Belegdatum
    row[13] = '"%s"' % text              # col 14 Buchungstext
    row[124] = taxkey                    # col 125 USt-Schlüssel
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--berater", required=True)
    ap.add_argument("--mandant", required=True)
    ap.add_argument("--wj-start", required=True, help="fiscal year start YYYYMMDD")
    ap.add_argument("--from-date", required=True, help="booking from YYYYMMDD")
    ap.add_argument("--to-date", required=True, help="booking to YYYYMMDD")
    ap.add_argument("--label", required=True)
    ap.add_argument("--skl", type=int, default=4, help="Sachkontenlaenge")
    ap.add_argument("--skr", default="03")
    ap.add_argument("--wkz", default="EUR")
    ap.add_argument("--absender", default="")
    ap.add_argument("--exported-by", default="")
    ap.add_argument("--imported-by", default="")
    ap.add_argument("--diktat", default="")
    ap.add_argument("--info", default="")
    ap.add_argument("--booking", action="append", required=True,
                    help="amount,side,account,taxkey,beleg,text")
    ap.add_argument("--output", required=True)
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    pinned = load_config(args.config)["datev-extf"]
    rows = [build_header(args, pinned)]
    for b in args.booking:
        rows.append(build_booking(b.split(",")))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="cp1252", newline="") as fh:
        w = csv.writer(fh, delimiter=DELIMITER, quoting=csv.QUOTE_MINIMAL)
        for r in rows:
            w.writerow(r)

    print(json.dumps({"ok": True, "output": str(out), "rows": len(rows),
                      "pinned_versionsnummer": pinned["extf_schema"]["version"].split("/")[0]},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
