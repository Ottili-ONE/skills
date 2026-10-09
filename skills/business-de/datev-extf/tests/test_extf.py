"""Tests for datev-extf scripts: build_stapel, fixture_generator, validate_extf."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS = ROOT / "business-de" / "datev-extf" / "scripts"
CONFIG = ROOT / "business-de" / "config" / "versions.json"


def run(script, *args, cwd=None):
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *args,
                        "--config", str(CONFIG)],
                       capture_output=True, text=True, cwd=cwd or ROOT)
    return r.returncode, r.stdout, r.stderr


# ---------------------------------------------------------------- validate_extf

def test_valid_fixture_passes(tmp_path):
    code, out, _ = run("fixture_generator.py", "--out-dir", str(tmp_path))
    assert code == 0
    code, out, _ = run("validate_extf.py", str(tmp_path / "buchungsstapel-valid.csv"))
    assert code == 0
    data = json.loads(out)
    assert data["ok"] is True
    assert data["pinned_versionsnummer"] == "700"
    assert data["pinned_formatversion"] == "13"
    assert data["error_count"] == 0


def test_broken_fixture_fails(tmp_path):
    code, _, _ = run("fixture_generator.py", "--out-dir", str(tmp_path))
    assert code == 0
    code, out, _ = run("validate_extf.py", str(tmp_path / "buchungsstapel-broken.csv"))
    assert code == 1
    data = json.loads(out)
    assert data["ok"] is False
    codes = {e["code"] for e in data["errors"]}
    assert "amount-dot-decimal" in codes
    assert "belegdatum-format" in codes


def test_build_stapel_validates(tmp_path):
    out = tmp_path / "stapel.csv"
    code, _, _ = run("build_stapel.py", "--berater", "29098", "--mandant", "55003",
                     "--wj-start", "20260101", "--from", "20260601", "--to", "20260630",
                     "--label", "Shop 06/2026", "--skr", "03",
                     "--booking", "1200,S,4000,0206,19,Netto+19%",
                     "--booking", "500,S,4200,0306,7,Netto+7%",
                     "--output", str(out))
    assert code == 0
    code, out, _ = run("validate_extf.py", str(out))
    assert code == 0
    data = json.loads(out)
    assert data["ok"] is True
    assert data["checked_lines"] == 3  # header + heading + 2 bookings


def test_dot_decimal_amount_is_error(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_bytes(b"EXTF;700;21;Buchungsstapel;13;20261009105214000\r\n"
                  b"Umsatz (ohne Soll/Haben-Kz)\r\n"
                  + b"12.50;S" + b";" * 123 + b"\r\n")
    code, out, err = run("validate_extf.py", str(f))
    assert code == 1
    data = json.loads(out)
    assert any(e["code"] == "amount-dot-decimal" for e in data["errors"])


def test_missing_file_returns_2(tmp_path):
    code, out, err = run("validate_extf.py", str(tmp_path / "nope.csv"))
    assert code == 2
    assert "file not found" in out + err


def test_tax_key_lands_at_column_97(tmp_path):
    """The Steuerschlüssel must sit at column 97 (index 96), not column 125.

    Verified 2026-10-09 against seamless-engineering/datev-extf
    src/columns.ts BUCHUNGSSTAPEL_COLUMNS: col 97 = "USt-Schlüssel
    (Anzahlungen)", col 125 = "Abw. Skontokonto". Writing the key at
    index 124 makes DATEV read it as "Abw. Skontokonto" and drop the tax
    key silently.
    """
    import sys
    sys.path.insert(0, str(SCRIPTS))
    from fixture_generator import booking
    row = booking("1200", "S", "4000", "0206", "Netto+19%")
    assert len(row) == 125
    assert row[96] == "19", f"tax key at col 97: {row[96]!r}"
    assert row[124] == "", f"col 125 must be empty, got {row[124]!r}"


def test_pinned_version_not_hardcoded():
    import re
    src = (SCRIPTS / "validate_extf.py").read_text(encoding="utf-8")
    assert "config/versions.json" in src
    # the module-level FORMAT_VERSION constant is the *fallback*, not a pin
    assert re.search(r'FORMAT_VERSION\s*=\s*"13"', src)

def _pad(n):
    return b";" * (n - 1)


def test_header_checks_catch_bad_values(tmp_path):
    """Header field checks (Berater/Mandant/WKZ/Sachkontenlaenge) verified
    2026-10-09 against seamless-engineering/datev-extf src/extf.ts."""
    f = tmp_path / "bad.csv"
    f.write_bytes(
        b"EXTF;700;21;Buchungsstapel;13;20261009105214000" + _pad(6) +
        b"99;0;20260101;9;20260601;20260630;Label" + _pad(15) +
        b"EUR" + _pad(6) + b"03" + _pad(5) + b"\r\n"
        b"Umsatz (ohne Soll/Haben-Kz)" + _pad(125) + b"\r\n"
        + b"12,50;S" + _pad(125) + b"\r\n")
    code, out, _ = run("validate_extf.py", str(f))
    assert code == 1
    data = json.loads(out)
    codes = {e["code"] for e in data["errors"]}
    assert "header-berater" in codes
    assert "header-mandant" in codes
    assert "header-skl" in codes


def test_header_dates_out_of_wj(tmp_path):
    """Datum vom/bis outside the WJ is an error, not a warning."""
    f = tmp_path / "bad.csv"
    f.write_bytes(
        b"EXTF;700;21;Buchungsstapel;13;20261009105214000" + _pad(6) +
        b"29098;55003;20260101;4;20270601;20270630;Label" + _pad(15) +
        b"EUR" + _pad(6) + b"03" + _pad(5) + b"\r\n"
        b"Umsatz (ohne Soll/Haben-Kz)" + _pad(125) + b"\r\n"
        + b"12,50;S" + _pad(125) + b"\r\n")
    code, out, _ = run("validate_extf.py", str(f))
    assert code == 1
    data = json.loads(out)
    assert any(e["code"] == "header-beyond-wj" for e in data["errors"])
