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
    r = run([{"account": "1200", "side": "S", "amount": 100, "tax_key": "19", "ref": "x"},
             {"account": "8000", "side": "H", "amount": 100, "tax_key": "19", "ref": "x"}])
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
    p.write_text("account,side,amount,tax_key\n1200,S,100,19\n8000,H,100,19\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
