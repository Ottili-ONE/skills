#!/usr/bin/env python3
"""Validate a DATEV EXTF Buchungsstapel (CSV, semicolon, cp1252, Formatversion 13).

Rules verified against seamless-engineering/datev-extf (src/extf.ts,
src/columns.ts, src/messages.ts, EXTF_AS_OF 2026-09-25). Emits a machine-
readable pass/fail JSON plus a list of findings with severity and code.

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


def add(findings, code, severity, line, field, value, params=None):
    f = {"code": code, "severity": severity, "line": line,
         "field": field, "value": value}
    if params:
        f["params"] = params
    findings.append(f)
