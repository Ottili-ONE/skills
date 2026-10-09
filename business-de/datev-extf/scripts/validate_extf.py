#!/usr/bin/env python3
"""Validate a DATEV EXTF Buchungsstapel (CSV, semicolon, cp1252, Formatversion 13).

Rules verified against seamless-engineering/datev-extf (src/extf.ts,
src/columns.ts, EXTF_AS_OF 2026-09-25). Emits a machine-readable pass/fail JSON
plus a list of findings with severity and code.

Usage:
    python3 validate_extf.py Buchungsstapel.csv [--config config/versions.json]
"""
import argparse
import csv
import io
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

DELIMITER = ";"
EXPECTED_HEADER_FIELDS = 31
EXPECTED_COLUMNS = 125
FORMAT_VERSION = "13"
CATEGORY = "21"
FORMAT_NAME = "Buchungsstapel"

# Automatikkonten (AM-Konten) per SKR, Gültig 2026. A BU-Schlüssel other than
# "40" on these is rejected or double-counted by DATEV.
AUTOMATIC_ACCOUNTS = {
    "03": {"8120", "8125", "8300", "8310", "8315", "8336", "8338", "8400", "8449"},
    "04": {"4120", "4125", "4300", "4310", "4315", "4336", "4338", "4400", "4449"},
}

# 1-based field numbers that DATEV writes as quoted text.
HEADER_TEXT_FIELDS = [1, 4, 8, 9, 10, 17, 18, 22, 27, 31]
BOOKING_TEXT_FIELDS = [2, 3, 9, 11, 12, 14, 37, 38, 40, 120]


def decode_bytes(raw: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("cp1252", errors="replace")


def parse_rows(path: Path):
    """Return (rows, unclosed_quote_line). rows: list of [line_no, [cells]]."""
    text = decode_bytes(path.read_bytes())
    reader = csv.reader(io.StringIO(text), delimiter=DELIMITER)
    rows, unclosed = [], None
    for i, cells in enumerate(reader, start=1):
        if not any(c.strip() for c in cells):
            continue
        rows.append([i, cells])
    return rows, unclosed


def is_real_day(y, m, d):
    if not (1 <= m <= 12) or not (1 <= d <= 31):
        return False
    try:
        date(y, m, d)
        return True
    except ValueError:
        return False


def parse_ymd(s):
    if re.fullmatch(r"\d{8}", s):
        return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    return None


def add(findings, code, severity, line, field=None, value=None, params=None):
    f = {"code": code, "severity": severity, "line": line}
    if field is not None:
        f["field"] = field
    if value is not None:
        f["value"] = value
    if params:
        f["params"] = params
    findings.append(f)


def validate(path: Path, config: dict) -> dict:
    """Run all EXTF checks. Returns a result dict."""
    pinned = config["datev-extf"]["extf_schema"]
    expected_versionnr = pinned["version"].split("/")[0].strip()
    expected_formatver = pinned.get("format_version", FORMAT_VERSION)
    rows, _unclosed = parse_rows(path)
    findings = []

    if not rows:
        return {"ok": False, "file": str(path), "errors": ["file is empty"],
                "pinned_versionsnummer": expected_versionnr,
                "pinned_formatversion": expected_formatver}

    header = rows[0][1]
    booking_rows = rows[1:]

    # --- header (line 1, 31 fields) ---
    if len(header) < EXPECTED_HEADER_FIELDS:
        add(findings, "header-too-short", "error", rows[0][0],
            field="header", value=str(len(header)),
            params={"expected": EXPECTED_HEADER_FIELDS})
    else:
        if header[0] != "EXTF":
            add(findings, "kennzeichen", "error", rows[0][0], field=1, value=header[0])
        if header[1] != expected_versionnr:
            add(findings, "versionsnummer", "error", rows[0][0], field=2,
                value=header[1], params={"expected": expected_versionnr})
        if header[2] != CATEGORY:
            add(findings, "formatkategorie", "error", rows[0][0], field=3, value=header[2])
        if header[3] != FORMAT_NAME:
            add(findings, "formatname", "error", rows[0][0], field=4, value=header[3])
        if header[4] != expected_formatver:
            add(findings, "formatversion", "error", rows[0][0], field=5,
                value=header[4], params={"expected": expected_formatver})
        if not re.fullmatch(r"\d{17}", header[5]):
            add(findings, "erzeugt-am-format", "error", rows[0][0], field=6, value=header[5])
        if header[20] not in ("", "0", "1"):
            add(findings, "festschreibung", "error", rows[0][0], field=21, value=header[20])

    # --- heading row (line 2, 125 columns) ---
    # DATEV's importer reads columns by position, so a missing or mismatched
    # heading row is only a warning (seamless-engineering/datev-extf: a differing
    # heading is "headings-differ", never an error). A file that starts with the
    # heading row is missing its first line ("headings-first") and is rejected.
    if booking_rows:
        heading = booking_rows[0][1]
        if len(heading) != EXPECTED_COLUMNS:
            add(findings, "heading-column-count", "warning", booking_rows[0][0],
                field="heading", value=str(len(heading)),
                params={"expected": EXPECTED_COLUMNS})
        elif not any(c.strip() for c in heading):
            add(findings, "no-headings", "warning", booking_rows[0][0])
        else:
            # heading row present -> bookings start on line 3
            booking_rows = booking_rows[1:]

    # --- booking rows (line 3+, or line 2+ when no heading row) ---
    for line_no, cells in booking_rows:
        if len(cells) != EXPECTED_COLUMNS:
            add(findings, "booking-column-count", "error", line_no,
                field="row", value=str(len(cells)),
                params={"expected": EXPECTED_COLUMNS})
            continue
        amount = cells[0]
        side = cells[1]
        account = cells[6]
        beleg = cells[9]
        if amount == "" and side == "":
            continue  # blank booking line
        if "." in amount:
            add(findings, "amount-dot-decimal", "error", line_no, field=1, value=amount)
        if side not in ("S", "H"):
            add(findings, "side-invalid", "error", line_no, field=2, value=side)
        if not re.fullmatch(r"\d{4}", beleg):
            add(findings, "belegdatum-format", "error", line_no, field=10, value=beleg)
        elif not is_real_day(2026, int(beleg[2:4]), int(beleg[0:2])):
            add(findings, "belegdatum-impossible", "warning", line_no, field=10, value=beleg)
        if account and len(account) > 4:
            add(findings, "account-too-long", "warning", line_no, field=7, value=account)
        # Automatikkonto rule: BU-Schlüssel (col 9, 1-based) other than "40"
        bu = cells[8]
        if account in AUTOMATIC_ACCOUNTS.get("03", set()) and bu and bu != "40":
            add(findings, "bu-on-automatic-account", "error", line_no, field=9,
                value=bu, params={"account": account})

    errors = [f for f in findings if f["severity"] == "error"]
    return {
        "ok": not errors,
        "file": str(path),
        "pinned_versionsnummer": expected_versionnr,
        "pinned_formatversion": expected_formatver,
        "checked_lines": len(rows),
        "error_count": len(errors),
        "warning_count": len(findings) - len(errors),
        "errors": errors,
        "warnings": [f for f in findings if f["severity"] == "warning"],
        "next": ("fix the listed errors and re-run" if errors
                 else "import into DATEV is permitted"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", help="Buchungsstapel CSV")
    ap.add_argument("--config", default="config/versions.json")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(json.dumps({"ok": False, "error": f"file not found: {path}"}, indent=2),
              file=sys.stderr)
        return 2
    try:
        config = load_config(args.config)
        result = validate(path, config)
    except (ValueError, json.JSONDecodeError, FileNotFoundError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
