"""Tests for validate_extf.py — offline, deterministic, no network."""
import csv
import io
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = ROOT / "skills" / "business-de" / "datev-extf" / "scripts" / "validate_extf.py"
CONFIG = ROOT / "skills" / "business-de" / "config" / "versions.json"


def run(args, csv_text):
    p = Path("/tmp/_extf_test.csv")
    p.write_text(csv_text, encoding="cp1252")
    r = subprocess.run([sys.executable, str(SCRIPT), str(p), "--config", str(CONFIG)],
                       capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout)


def header(label="T", version="13"):
    return ["EXTF", "700", "21", "Buchungsstapel", version, "20261008",
            "", "", "", "", "29098", "55003", "20260101", "4",
            "20260601", "20260630", label, "", "1", "EUR", "", "", "",
            "03", "", "", "", "", "", "", ""]


def row(amount="1200", side="S", acct="4000", beleg="20260601", text="Netto+19%"):
    r = [""] * 125
    r[0], r[1], r[6], r[9], r[13] = amount, side, acct, beleg, text
    return r


def csv_of(rows):
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")
    for r in rows:
        w.writerow(r)
    return out.getvalue()


def test_valid_stapel():
    code, data = run([], csv_of([header(), row()]))
    assert code == 0, data
    assert data["ok"] is True
    assert data["errors"] == []


def test_dot_decimal_is_error():
    code, data = run([], csv_of([header(), row(amount="12.50")]))
    assert code == 1
    codes = {e["code"] for e in data["errors"]}
    assert "AMOUNT_DECIMAL_SEPARATOR" in codes


def test_bad_belegdatum():
    code, data = run([], csv_of([header(), row(beleg="2026601")]))
    assert code == 1
    codes = {e["code"] for e in data["errors"]}
    assert "BELEGDATEUM_INVALID" in codes


def test_bu_schluessel_on_automatikkonto():
    r = row(acct="8120")
    r[8] = "99"
    code, data = run([], csv_of([header(), r]))
    assert code == 1
    codes = {e["code"] for e in data["errors"]}
    assert "BU_SCHLUESSEL_ON_AUTOMATIKKONTO" in codes


def test_header_wrong_formatversion():
    code, data = run([], csv_of([header(version="12"), row()]))
    assert code == 1
    codes = {e["code"] for e in data["errors"]}
    assert "HEADER_FORMATVERSION" in codes


def test_header_missing_kennzeichen():
    h = header()
    h[0] = ""
    code, data = run([], csv_of([h, row()]))
    assert code == 1
    codes = {e["code"] for e in data["errors"]}
    assert "HEADER_KENNZEICHEN" in codes


def test_account_too_long():
    code, data = run([], csv_of([header(), row(acct="400000")]))
    assert code == 1
    codes = {e["code"] for e in data["errors"]}
    assert "ACCOUNT_LENGTH" in codes


def test_missing_steuerschluessel():
    r = row()
    r[96] = ""
    code, data = run([], csv_of([header(), r]))
    assert code == 1
    codes = {e["code"] for e in data["errors"]}
    assert "STEUERSCHLUESSEL_MISSING" in codes


def test_machine_readable_output():
    code, data = run([], csv_of([header(), row()]))
    assert "pinned_versionsnummer" in data
    assert data["pinned_versionsnummer"] == "700"
    assert "validator_tag" in data
