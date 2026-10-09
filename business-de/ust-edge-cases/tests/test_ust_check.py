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


def test_reverse_charge_on_goods_rejected():
    # §3g is services only; claiming reverse charge on a goods supply is rejected.
    r = run([{"tax_key": "06/0", "net": 100.0, "tax_amount": 0.0,
              "customer_vat_id": "DE123456789",
              "reverse_charge": True, "supply_type": "goods"}])
    assert r.returncode == 2 and "services only" in r.stderr


def test_reverse_charge_on_service_accepted():
    # §3g reverse charge on a service with a valid buyer USt-IdNr. is valid.
    r = run([{"tax_key": "06/0", "net": 100.0, "tax_amount": 0.0,
              "customer_vat_id": "DE123456789",
              "reverse_charge": True, "supply_type": "service"}])
    assert r.returncode == 0, r.stderr


def test_intra_eu_goods_without_reverse_charge_claim_accepted():
    # Intra-EU goods (§4a) use 06/0 without claiming reverse charge.
    r = run([{"tax_key": "06/0", "net": 100.0, "tax_amount": 0.0,
              "customer_vat_id": "DE123456789",
              "reverse_charge": False, "supply_type": "goods"}])
    assert r.returncode == 0, r.stderr


def test_zero_rate_carrying_tax_amount_rejected():
    r = run([{"tax_key": "06/0", "net": 100.0, "tax_amount": 5.0,
              "customer_vat_id": "DE123456789"}])
    assert r.returncode == 2


def test_kleinbetagsrechnung_flagged_as_einvoice():
    # 19.90 gross < 250 -> Kleinbetagsrechnung, exempt from e-invoicing.
    r = run([{"tax_key": "19", "net": 16.72, "tax_amount": 3.18, "e_invoice": True}])
    assert r.returncode == 2 and "Kleinbetagsrechnung" in r.stderr


def test_kleinbetagsrechnung_ok_as_sonstige():
    r = run([{"tax_key": "19", "net": 16.72, "tax_amount": 3.18, "e_invoice": False}])
    assert r.returncode == 0, r.stderr


def test_unrounded_tax_amount_rejected():
    r = run([{"tax_key": "19", "net": 33.33, "tax_amount": 6.3326}])
    assert r.returncode == 2


def test_rounded_tax_amount_accepted():
    r = run([{"tax_key": "19", "net": 33.33, "tax_amount": 6.33}])
    assert r.returncode == 0, r.stderr


def test_kleinunternehmer_zero_rate_rejected():
    r = run({"lines": [{"tax_key": "06/0", "net": 100.0, "tax_amount": 0.0,
                        "customer_vat_id": "DE123456789"}],
             "kleinunternehmer": True, "prior_turnover": 10000.0})
    assert r.returncode == 2
