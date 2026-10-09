import json, subprocess, sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "journal_check.py"
TMP = Path(__file__).resolve().parent / "tmp"
TMP.mkdir(exist_ok=True)


def run(payload):
    p = TMP / "j.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)


def test_balanced():
    r = run([{"account": "1200", "side": "S", "amount": 119, "tax_key": "19", "ref": "x"},
             {"account": "8000", "side": "H", "amount": 100, "tax_key": "19", "ref": "x"},
             {"account": "1570", "side": "H", "amount": 19, "tax_key": "19", "ref": "tax"}])
    assert r.returncode == 0, r.stderr


def test_unbalanced():
    r = run([{"account": "1200", "side": "S", "amount": 100, "tax_key": "19"},
             {"account": "8000", "side": "H", "amount": 99, "tax_key": "19"}])
    assert r.returncode == 2


def test_bad_tax_key():
    r = run([{"account": "1200", "side": "S", "amount": 100, "tax_key": "99"},
             {"account": "8000", "side": "H", "amount": 100, "tax_key": "19"}])
    assert r.returncode == 2


def test_csv_input():
    p = TMP / "j.csv"
    p.write_text("account,side,amount,tax_key\n1200,S,119,19\n8000,H,100,19\n1570,H,19,19\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_revenue_tax_key_without_tax_account():
    # 19% on revenue 8000 but no 1570 line -> plausibility failure.
    # The 19.00 goes to a non-tax asset account (1190) so the journal still
    # balances; only the tax-account-presence rule must fire.
    r = run([{"account": "1200", "side": "S", "amount": 119, "tax_key": "19"},
             {"account": "8000", "side": "H", "amount": 100, "tax_key": "19"},
             {"account": "1190", "side": "H", "amount": 19, "tax_key": "19"}])
    assert r.returncode == 2 and "tax account" in r.stderr


def test_empty_journal_rejected():
    p = TMP / "empty.json"
    p.write_text("[]", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)
    assert r.returncode == 2 and "empty" in r.stderr


def test_account_outside_skr_ranges():
    r = run([{"account": "3300", "side": "S", "amount": 100, "tax_key": "19"},
             {"account": "8000", "side": "H", "amount": 100, "tax_key": "19"}])
    assert r.returncode == 2 and "outside SKR" in r.stderr


def test_tax_account_netting_satisfied():
    # 19% revenue with a 1570 Haben line of 19 -> passes
    r = run([{"account": "1200", "side": "S", "amount": 119, "tax_key": "19"},
             {"account": "8000", "side": "H", "amount": 100, "tax_key": "19"},
             {"account": "1570", "side": "H", "amount": 19, "tax_key": "19"}])
    assert r.returncode == 0, r.stderr
