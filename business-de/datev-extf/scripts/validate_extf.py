#!/usr/bin/env python3
"""Validate a DATEV EXTF Buchungsstapel (CSV, semicolon-delimited, Windows-1252).

Emits a machine-readable pass/fail JSON plus the list of failed fields.
Reads the pinned Versionsnummer/Formatversion from config/versions.json and
never hardcodes a version.

Usage:
    python3 validate_extf.py Buchungsstapel.csv [--config config/versions.json]
"""
import argparse
import csv
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

DELIMITER = ";"
EXPECTED_HEADER_COUNT = 31
EXPECTED_FORMAT_NAME = "Buchungsstapel"
EXPECTED_CATEGORY = "21"


def decode_bytes(raw: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("cp1252", errors="replace")


def read_rows(path: Path):
    text = decode_bytes(path.read_bytes())
    reader = csv.reader(io.StringIO(text), delimiter=DELIMITER)
    return [r for r in reader if any(c.strip() for c in r)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", help="EXTF CSV file")
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(json.dumps({"ok": False, "error": "file not found: " + str(path)}))
        return 2

    pinned = load_config(args.config)["datev-extf"]
    rows = read_rows(path)
    errors = []
    warnings = []

    if not rows:
        errors.append("file is empty")
    else:
        header = rows[0]
        if len(header) < EXPECTED_HEADER_COUNT:
            errors.append("header has %d fields, expected %d" %
                          (len(header), EXPECTED_HEADER_COUNT))
        if header and header[0].strip() != "EXTF":
            errors.append("field 1 Kennzeichen must be 'EXTF', got '%s'" % header[0])
        if len(header) > 1 and header[1].strip() != pinned["extf_schema"]["version"].split("/")[0].strip():
            errors.append("field 2 Versionsnummer must be %s" %
                          pinned["extf_schema"]["version"].split("/")[0].strip())
        if len(header) > 2 and header[2].strip() != EXPECTED_CATEGORY:
            errors.append("field 3 Formatkategorie must be '%s'" % EXPECTED_CATEGORY)
        if len(header) > 3 and header[3].strip() != EXPECTED_FORMAT_NAME:
            errors.append("field 4 Formatname must be '%s'" % EXPECTED_FORMAT_NAME)
        if len(header) > 4 and header[4].strip() != "13":
            errors.append("field 5 Formatversion must be '13'")

        for i, row in enumerate(rows[1:], start=2):
            if len(row) < 8:
                errors.append("line %d: row has %d fields, expected >= 8" % (i, len(row)))
                continue
            amount = row[0].strip()
            side = row[1].strip()
            konto = row[6].strip()
            beleg = row[9].strip()
            if side not in ("S", "H"):
                errors.append("line %d: field 2 Soll/Haben must be 'S' or 'H'" % i)
            if "," in amount and "." in amount:
                errors.append("line %d: amount '%s' has both separators" % (i, amount))
            elif "." in amount:
                errors.append("line %d: amount '%s' uses a dot; DATEV expects a comma" % (i, amount))
            if beleg and len(beleg) < 8:
                warnings.append("line %d: Belegdatum '%s' looks too short" % (i, beleg))
            if beleg and not (beleg.isdigit() and len(beleg) == 8):
                errors.append("line %d: Belegdatum must be YYYYMMDD, got '%s'" % (i, beleg))
            if konto and len(konto) > 4:
                warnings.append("line %d: Konto '%s' exceeds the default Sachkontenlaenge of 4" % (i, konto))

    ok = not errors
    print(json.dumps({
        "ok": ok,
        "pinned_versionsnummer": pinned["extf_schema"]["version"].split("/")[0].strip(),
        "pinned_formatversion": "13",
        "file": str(path),
        "rows": len(rows),
        "errors": errors,
        "warnings": warnings,
        "next": ("fix the listed errors and re-run" if errors else "validated"),
    }, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
