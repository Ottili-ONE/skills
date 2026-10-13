"""Datenservices validation-error edge cases for validate_extf.py.

These cover the error codes an agent must not suppress: wrong Versionsnummer,
wrong Formatkategorie, comma-vs-dot decimals, Soll/Haben-Kennzeichen mismatch
and the WJ-arithmetic rule (WJ end = wjDate + 1y - 1d).
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS = ROOT / "business-de" / "datev-extf" / "scripts"
CONFIG = ROOT / "business-de" / "config" / "versions.json"


def run(script, *args):
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *args,
                        "--config", str(CONFIG)],
                       capture_output=True, text=True, cwd=ROOT)
    return r.returncode, r.stdout, r.stderr


def _read_valid(tmp_path):
    # generate the fixture first (it is the baseline every mutation is applied to)
    run("fixture_generator.py", "--out-dir", str(tmp_path))
    p = tmp_path / "buchungsstapel-valid.csv"
    return p.read_text(encoding="cp1252")


def test_wrong_versionsnummer_is_blocking(tmp_path):
    src = _read_valid(tmp_path).replace(";700;", ";699;")
    bad = tmp_path / "bad.csv"
    bad.write_text(src, encoding="cp1252")
    code, out, _ = run("validate_extf.py", str(bad))
    assert code == 1
    data = json.loads(out)
    codes = {e["code"] for e in data["errors"]}
    assert any("versionsnummer" in c.lower() for c in codes)


def test_wrong_category_is_blocking(tmp_path):
    """Formatkategorie 16 (Debitoren/Kreditoren) instead of 21 (Buchungsstapel)."""
    src = _read_valid(tmp_path).replace(";21;", ";16;")
    bad = tmp_path / "bad.csv"
    bad.write_text(src, encoding="cp1252")
    code, out, _ = run("validate_extf.py", str(bad))
    assert code == 1
    codes = {e["code"] for e in json.loads(out)["errors"]}
    assert any("category" in c.lower() or "formatkategorie" in c.lower() for c in codes)


def test_comma_decimal_required(tmp_path):
    """A dot decimal (1.500,00) is the classic import rejection; the fixture
    writes the net amount in column 1 of the booking row."""
    lines = _read_valid(tmp_path).splitlines()
    lines[2] = lines[2].replace("1200", "1.500")  # dot decimal in col 1
    bad = tmp_path / "bad.csv"
    bad.write_text("\n".join(lines) + "\n", encoding="cp1252")
    code, out, _ = run("validate_extf.py", str(bad))
    assert code == 1
    codes = {e["code"] for e in json.loads(out)["errors"]}
    assert any("decimal" in c.lower() for c in codes)


def test_soll_haben_invalid_value_is_blocking(tmp_path):
    """Soll/Haben-Kennzeichen (col 2 of the booking row) must be exactly S or H.
    A third value is rejected as `side-invalid`; a sign-vs-amount mismatch is
    NOT checked by this offline subset (DATEV catches it at import) and is
    documented in the SKILL.md pitfalls."""
    lines = _read_valid(tmp_path).splitlines()
    cols = lines[2].split(";")
    cols[1] = "X"  # neither S nor H
    lines[2] = ";".join(cols)
    bad = tmp_path / "bad.csv"
    bad.write_text("\n".join(lines) + "\n", encoding="cp1252")
    code, out, _ = run("validate_extf.py", str(bad))
    assert code == 1
    codes = {e["code"] for e in json.loads(out)["errors"]}
    assert "side-invalid" in codes


def test_wj_end_arithmetic(tmp_path):
    """WJ 2026-01-01 must end 2026-12-31 (wjDate + 1y - 1d), not 2026-01-01."""
    src = _read_valid(tmp_path).replace("20260101", "20261231")  # header WJ-Ende
    bad = tmp_path / "bad.csv"
    bad.write_text(src, encoding="cp1252")
    code, out, _ = run("validate_extf.py", str(bad))
    assert code == 1
    codes = {e["code"] for e in json.loads(out)["errors"]}
    assert any("wj" in c.lower() for c in codes)


def test_belegdatum_is_ttmm_not_yyyymmdd(tmp_path):
    """Belegdatum (col 10) is TTMM; 20260602 is not a valid Belegdatum."""
    src = _read_valid(tmp_path).replace("0206", "20260602")
    bad = tmp_path / "bad.csv"
    bad.write_text(src, encoding="cp1252")
    code, out, _ = run("validate_extf.py", str(bad))
    assert code == 1
    codes = {e["code"] for e in json.loads(out)["errors"]}
    assert any("belegdatum" in c.lower() for c in codes)
