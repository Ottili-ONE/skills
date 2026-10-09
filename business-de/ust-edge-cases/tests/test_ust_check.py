import json, subprocess, sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "ust_check.py"
TMP = Path(__file__).resolve().parent / "tmp"
TMP.mkdir(exist_ok=True)


def run(data):
    p = TMP / "inv.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)


def test_standard_rate():
    r = run([{"tax_key": "19", "net": 100.0, "tax_amount": 19.0, "customer_vat_id": ""}])
    assert r.returncode == 0, r.stderr


def test_intra_eu_missing_idnr():
    r = run([{"tax_key": "06/0", "net": 100.0, "tax_amount": 0.0, "customer_vat_id": ""}])
    assert r.returncode == 2


def test_intra_eu_with_idnr():
    r = run([{"tax_key": "06/0", "net": 100.0, "tax_amount": 0.0, "customer_vat_id": "DE123456789"}])
    assert r.returncode == 0, r.stderr


def test_wrong_tax_amount():
    r = run([{"tax_key": "19", "net": 100.0, "tax_amount": 18.0, "customer_vat_id": ""}])
    assert r.returncode == 2


def test_kleinunternehmer_charging_vat():
    r = run({"lines": [{"tax_key": "19", "net": 100.0, "tax_amount": 19.0, "customer_vat_id": ""}],
             "kleinunternehmer": True, "prior_turnover": 10000.0})
    assert r.returncode == 2
