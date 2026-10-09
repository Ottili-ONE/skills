#!/usr/bin/env python3
"""Generate deterministic DATEV EXTF test fixtures: a valid Buchungsstapel and a
deliberately broken one for negative testing. Runnable offline.

Usage:
    python3 fixture_generator.py --out-dir ./fixtures
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402


# Line 2 of a DATEV Buchungsstapel: the 125-column heading row, copied
# verbatim from DATEV's Musterdaten (Formatversion 13) as corroborated by
# seamless-engineering/datev-extf src/columns.ts (EXTF_AS_OF 2026-09-25).
# The full list lives in heading_row.py; this module imports it.
from heading_row import HEADING_ROW  # noqa: E402


def header(label):
    return [
        "EXTF", "700", "21", "Buchungsstapel", "13", "20261008000000000",
        "", "", "", "", "29098", "55003", "20260101", "4",
        "20260601", "20260630", label, "", "1", "EUR", "", "", "",
        "03", "", "", "", "", "", "", "",
    ]


def booking(amount, side, account, beleg, text):
    row = [""] * 125
    row[0] = amount
    row[1] = side
    row[6] = account
    row[9] = beleg
    row[13] = text
    # col 97 (index 96) = "USt-Schlüssel (Anzahlungen)" — the tax key.
    # Verified 2026-10-09 against seamless-engineering/datev-extf
    # src/columns.ts BUCHUNGSSTAPEL_COLUMNS (EXTF_AS_OF 2026-09-25).
    # col 125 is "Abw. Skontokonto", NOT the tax key — an earlier draft
    # put the Steuerschlüssel at index 124, which DATEV would read as
    # "Abw. Skontokonto" and silently drop the real tax key.
    row[96] = "19"
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default="./fixtures")
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    pinned = load_config(args.config)["datev-extf"]
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    import csv
    valid_path = out / "buchungsstapel-valid.csv"
    broken_path = out / "buchungsstapel-broken.csv"

    with valid_path.open("w", encoding="cp1252", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(header("Fixture 06/2026"))
        w.writerow(HEADING_ROW)
        w.writerow(booking("1200", "S", "4000", "0206", "Netto+19%"))
        w.writerow(booking("500", "S", "4200", "0306", "Netto+7%"))

    with broken_path.open("w", encoding="cp1252", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(header("Fixture-broken 06/2026"))
        w.writerow(HEADING_ROW)
        # dot instead of comma, and a malformed Belegdatum
        w.writerow(booking("12.50", "S", "4000", "2026601", "Netto+19%"))

    print(json.dumps({
        "ok": True,
        "out_dir": str(out),
        "valid": str(valid_path),
        "broken": str(broken_path),
        "pinned_versionsnummer": pinned["extf_schema"]["version"].split("/")[0],
        "broken_fixtures": [
            {"file": str(broken_path),
             "expected_errors": [
                 "amount uses a dot; DATEV expects a comma",
                 "Belegdatum must be YYYYMMDD",
             ]},
        ],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
