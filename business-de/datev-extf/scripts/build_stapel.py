#!/usr/bin/env python3
"""Build a DATEV EXTF Buchungsstapel CSV (semicolon, cp1252, Formatversion 13).

Column and rule layout verified against seamless-engineering/datev-extf
(src/columns.ts, src/extf.ts, EXTF_AS_OF 2026-09-25). 125 booking columns;
USt-Schlüssel is column 97, Buchungs GUID is column 103, Herkunft-Kz is
column 102, Festschreibung is header field 21. Belegdatum (column 10) is
TTMM (day+month, 4 digits) — the year comes from the header, not the row.

Usage:
    python3 build_stapel.py --berater 29098 --mandant 55003 --wj-start 20260101 \
        --from 20260601 --to 20260630 --label "Shop 06/2026" --skr 03 \
        --booking 1200,S,4000,19,0206,Netto+19% \
        --output stapel.csv
"""
import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

DELIMITER = ";"
HEADER_FIELDS = 31
BOOKING_COLUMNS = 125
FORMAT_VERSION = "13"
CATEGORY = "21"
FORMAT_NAME = "Buchungsstapel"

# Automatikkonten (AM-Konten) per SKR: a BU-Schlüssel other than "40" on
# these is rejected or double-counted by DATEV. Verified 2026-10-08 against
# seamless-engineering/datev-extf src/extf.ts automaticAccounts (Gültig 2026).
AUTOMATIC_ACCOUNTS = {
    "03": {"8120", "8125", "8300", "8310", "8315", "8336", "8338", "8400", "8449"},
    "04": {"4120", "4125", "4300", "4310", "4315", "4336", "4338", "4400", "4449"},
}


def build_header(args, pinned) -> list:
    today = datetime.now().strftime("%Y%m%d%H%M%S000")  # 17-digit Erzeugt am (YYYYMMDDHHMMSS000)
    row = [""] * HEADER_FIELDS
    row[0] = "EXTF"
    row[1] = pinned["extf_schema"]["version"].split("/")[0].strip()
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
    row[20] = "1"          # Festschreibung (header field 21)
    row[21] = args.wkz or "EUR"
    row[26] = args.skr or ""
    row[30] = args.info or ""
    return row


def build_booking(parts: list, skr: str) -> list:
    """Map a booking spec to the 125-column row.

    Spec: amount,side,account,belegdatum(TTMM),taxkey,text[,costcenter]
    """
    if len(parts) < 6:
        raise SystemExit("booking must be amount,side,account,belegdatum,"
                         "taxkey,text[,costcenter]")
    amount, side, account, beleg, taxkey, text = parts[:6]
    costcenter = parts[6] if len(parts) > 6 else ""

    row = [""] * BOOKING_COLUMNS
    row[0] = amount.replace(".", ",")      # col 1  Umsatz (ohne Soll/Haben-Kz)
    row[1] = side                          # col 2  Soll/Haben-Kennzeichen
    row[6] = account                       # col 7  Konto
    row[9] = beleg                         # col 10 Belegdatum (TTMM)
    row[13] = text                         # col 14 Buchungstext
    row[36] = costcenter                   # col 37 KOST1 - Kostenstelle
    row[96] = taxkey                       # col 97 USt-Schlüssel (Anzahlungen)
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
                    help="amount,side,account,belegdatum(TTMM),taxkey,text[,costcenter]")
    ap.add_argument("--output", required=True)
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    pinned = load_config(args.config)["datev-extf"]
    rows = [build_header(args, pinned)]
    for b in args.booking:
        rows.append(build_booking(b.split(","), args.skr))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="cp1252", newline="") as fh:
        w = csv.writer(fh, delimiter=DELIMITER, quoting=csv.QUOTE_MINIMAL)
        for r in rows:
            w.writerow(r)

    print(json.dumps({"ok": True, "output": str(out), "rows": len(rows),
                      "pinned_versionsnummer": pinned["extf_schema"]["version"].split("/")[0].strip()},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
