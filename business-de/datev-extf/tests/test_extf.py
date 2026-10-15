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
    assert data["checked_lines"] == 4  # header + heading + 2 bookings


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


def _build_skr04_stapel(tmp_path):
    """Build a valid SKR 04 stapel via build_stapel, then swap the account
    for an Automatikkonto of SKR 04 (4120)."""
    out = tmp_path / "stapel.csv"
    code, _, _ = run("build_stapel.py", "--config", str(CONFIG),
                     "--berater", "29098", "--mandant", "55003",
                     "--wj-start", "20260101", "--from", "20260601",
                     "--to", "20260630", "--label", "Shop", "--skr", "04",
                     "--booking", "1200,S,4120,0206,19,Netto+19%",
                     "--output", str(out))
    assert code == 0
    return out


def test_skr_aware_automatic_account_check(tmp_path):
    """The Automatikkonto rule is SKR-aware. Earlier drafts only ever
    checked SKR 03, so an AM account in SKR 04 sailed through. Verified
    2026-10-08 against seamless-engineering/datev-extf src/extf.ts
    automaticAccounts (SKR 04 AM set: 4120, 4125, 4300, 4310, 4315, 4336,
    4338, 4400, 4449)."""
    out = _build_skr04_stapel(tmp_path)
    code, out_json, _ = run("validate_extf.py", str(out), "--config", str(CONFIG))
    assert code == 1, out_json
    data = json.loads(out_json)
    assert any(e["code"] == "bu-on-automatic-account" for e in data["errors"]), data["errors"]


def test_taxkey_missing_is_error(tmp_path):
    """A booking line without a Steuerschlüssel at column 97 fails."""
    out = tmp_path / "bad.csv"
    code, _, _ = run("build_stapel.py", "--config", str(CONFIG),
                     "--berater", "29098", "--mandant", "55003",
                     "--wj-start", "20260101", "--from", "20260601",
                     "--to", "20260630", "--label", "Shop", "--skr", "03",
                     "--booking", "1200,S,4000,0206,,Netto",
                     "--output", str(out))
    assert code == 0
    code, out_json, _ = run("validate_extf.py", str(out), "--config", str(CONFIG))
    assert code == 1, out_json
    data = json.loads(out_json)
    assert any(e["code"] == "taxkey-missing" for e in data["errors"]), data["errors"]


def test_build_stapel_zero_pads_taxkey(tmp_path):
    """build_stapel normalises the Steuerschlüssel to two digits, so "7"
    and "07" both produce a valid row."""
    out = tmp_path / "stapel.csv"
    code, _, _ = run("build_stapel.py", "--config", str(CONFIG),
                     "--berater", "29098", "--mandant", "55003",
                     "--wj-start", "20260101", "--from", "20260601",
                     "--to", "20260630", "--label", "Shop", "--skr", "03",
                     "--booking", "500,S,4200,0306,7,Netto+7%",
                     "--output", str(out))
    assert code == 0
    code, out, _ = run("validate_extf.py", str(out), "--config", str(CONFIG))
    assert code == 0, out
    import sys
    sys.path.insert(0, str(SCRIPTS))
    from build_stapel import build_booking
    row = build_booking("500,S,4200,0306,7,Netto+7%".split(","), "03")
    assert row[96] == "07", row[96]
