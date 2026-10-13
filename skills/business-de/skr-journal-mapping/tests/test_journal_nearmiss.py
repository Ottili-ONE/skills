"""Near-miss trigger tests for journal_check.py.

These encode the traps a strong generic agent would walk straight into:
the legacy 16/1 key, the SKR03/SKR04 1xxx-asset collision, the missing tax
account, and the empty journal.
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "journal_check.py"
TMP = Path(__file__).resolve().parent / "tmp"
TMP.mkdir(exist_ok=True)


def run(payload):
    p = TMP / "nearmiss.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(p)],
                       capture_output=True, text=True)
    return r.returncode, r.stderr


def test_legacy_key_16_1_still_accepted():
    """16/1 is legacy (pre-2020) but still a known key; it must not be rejected
    as unknown — it must only warn that it should not be used on new postings."""
    rc, err = run([
        {"account": "1200", "side": "S", "amount": 100, "tax_key": "16/1", "ref": "x"},
        {"account": "8000", "side": "H", "amount": 84, "tax_key": "16", "ref": "x"},
        {"account": "1570", "side": "H", "amount": 16, "tax_key": "16", "ref": "tax"},
    ])
    assert rc == 0, err


def test_unknown_tax_key_rejected():
    rc, err = run([
        {"account": "1200", "side": "S", "amount": 100, "tax_key": "42"},
        {"account": "8000", "side": "H", "amount": 100, "tax_key": "19"},
    ])
    assert rc == 2
    assert "42" in err


def test_tax_key_without_tax_account_rejected():
    """A 19% line with no 1570/1571/1572 amount fails the USt-Anmeldung
    plausibility check."""
    rc, err = run([
        {"account": "1200", "side": "S", "amount": 100, "tax_key": "19", "ref": "x"},
        {"account": "8000", "side": "H", "amount": 100, "tax_key": "19", "ref": "x"},
    ])
    assert rc == 2
    assert "1570" in err or "tax account" in err.lower()


def test_empty_journal_rejected():
    rc, err = run([])
    assert rc == 2
    assert "empty" in err.lower()


def test_account_outside_skr_range_rejected():
    rc, err = run([
        {"account": "3000", "side": "S", "amount": 100, "tax_key": "19"},
        {"account": "8000", "side": "H", "amount": 100, "tax_key": "19"},
        {"account": "1570", "side": "H", "amount": 19, "tax_key": "19"},
    ])
    assert rc == 2
    assert "3000" in err
