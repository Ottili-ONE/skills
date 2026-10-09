#!/usr/bin/env python3
"""Validate a DATEV EXTF Buchungsstapel (CSV, semicolon, cp1252, Formatversion 13).

Rules verified against seamless-engineering/datev-extf (src/extf.ts,
src/columns.ts, src/messages.ts, EXTF_AS_OF 2026-09-25, fetched 2026-10-08).
Emits a machine-readable pass/fail JSON plus a list of findings with severity
and code. Every error is blocking; warnings are reported but do not fail.

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
CATEGORY = "21"
FORMAT_NAME = "Buchungsstapel"

# Automatikkonten (AM-Konten) per SKR, Gultig 2026. A BU-Schlüssel other than
# "40" on these is rejected or double-counted by DATEV (bu-automatic).
AUTOMATIC_ACCOUNTS = {
    "03": {"8120", "8125", "8300", "8310", "8315", "8336", "8338", "8400", "8449"},
    "04": {"4120", "4125", "4300", "4310", "4315", "4336", "4338", "4400", "4449"},
}

# 1-based field numbers that DATEV writes as quoted text.
HEADER_TEXT_FIELDS = [1, 4, 8, 9, 10, 17, 18, 22, 27, 31]
BOOKING_TEXT_FIELDS = [2, 3, 9, 11, 12, 14, 37, 38, 40, 120]

# 0-based column indices used by the row checks.
COL_AMOUNT, COL_SIDE, COL_CURRENCY, COL_KONTO, COL_GEGENKONTO, COL_BU = 0, 1, 2, 6, 7, 8
COL_BELEG, COL_BELEG1, COL_TEXT, COL_KOST1, COL_UST = 9, 10, 13, 36, 96
