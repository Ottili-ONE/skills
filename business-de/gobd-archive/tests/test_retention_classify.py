"""Tests for retention_classify.py: class mapping, end-date math, error paths."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "retention_classify.py"
CONFIG = Path(__file__).resolve().parent.parent.parent.parent / "business-de" / "config" / "versions.json"


def run(args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args, "--config", str(CONFIG), "--json"],
                       capture_output=True, text=True)
    blob = r.stdout if r.stdout else r.stderr
    return r.returncode, json.loads(blob)


def test_invoice_8_years():
    code, out = run(["--type", "invoice", "--year", "2026"])
    assert code == 0 and out["ok"]
    assert out["retention_class"] == "Buchungsbeleg"
    assert out["retention_years"] == 8
    assert out["retention_end"] == "2034-12-31"


def test_annual_account_10_years():
    code, out = run(["--type", "annual-account", "--year", "2024"])
    assert code == 0 and out["ok"]
    assert out["retention_class"] == "Bücher / Jahresabschluss"
    assert out["retention_end"] == "2034-12-31"


def test_correspondence_6_years():
    code, out = run(["--type", "correspondence", "--year", "2026"])
    assert code == 0 and out["ok"]
    assert out["retention_end"] == "2032-12-31"


def test_unknown_type_errors():
    code, out = run(["--type", "banana", "--year", "2026"])
    assert code == 2
    assert "unknown document type" in out["error"]
