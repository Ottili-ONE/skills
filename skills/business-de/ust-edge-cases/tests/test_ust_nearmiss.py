"""Near-miss trigger tests for ust_check.py.

The traps: reverse charge on a GOODS supply (must be services only),
Kleinunternehmer over the EUR 20,000 threshold, cent rounding, and the
Kleinbetagsrechnung / e-invoice interplay. The checker's contract is
check(rows, prior_turnover, kleinunternehmer) with rows carrying net/tax_amount.
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "ust_check.py"
TMP = Path(__file__).resolve().parent / "tmp"
TMP.mkdir(exist_ok=True)


def run(data):
    p = TMP / "nearmiss.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(p)],
                       capture_output=True, text=True)
    return r.returncode, r.stderr


def test_reverse_charge_on_goods_rejected():
    """§13b reverse charge is services only. A goods supply with a buyer
    USt-IdNr. is 0% under §4a, NOT reverse charge."""
    rc, err = run([{
        "tax_key": "06/0", "net": 1000.00, "tax_amount": 0.00,
        "customer_vat_id": "DE1234567890123",
        "supply_type": "goods", "reverse_charge": True,
    }])
    assert rc == 2
    assert "services only" in err


def test_reverse_charge_on_services_accepted():
    rc, err = run([{
        "tax_key": "06/0", "net": 1000.00, "tax_amount": 0.00,
        "customer_vat_id": "DE1234567890123",
        "supply_type": "service", "reverse_charge": True,
    }])
    assert rc == 0, err


def test_kleinunternehmer_over_threshold_rejected():
    """UStG §19: prior-year turnover must be <= EUR 20,000."""
    rc, err = run({
        "prior_turnover": 25000,
        "kleinunternehmer": True,
        "lines": [{
            "tax_key": "0", "net": 100.00, "tax_amount": 0.00,
            "supply_type": "goods",
        }]
    })
    assert rc == 2
    assert "20000" in err or "threshold" in err.lower()


def test_kleinunternehmer_under_threshold_accepted():
    rc, err = run({
        "prior_turnover": 19000,
        "kleinunternehmer": True,
        "lines": [{
            "tax_key": "0", "net": 100.00, "tax_amount": 0.00,
            "supply_type": "goods",
        }]
    })
    assert rc == 0, err


def test_kleinunternehmer_cannot_charge_vat():
    """A Kleinunternehmer with a taxed key (19%) is rejected."""
    rc, err = run({
        "prior_turnover": 19000,
        "kleinunternehmer": True,
        "lines": [{
            "tax_key": "19", "net": 100.00, "tax_amount": 19.00,
            "supply_type": "goods",
        }]
    })
    assert rc == 2
    assert "Kleinunternehmer" in err


def test_rounding_to_cents():
    """UStDV §23: tax amounts round to cents, 0.5-up."""
    rc, err = run([{
        "tax_key": "19", "net": 100.00, "tax_amount": 19.00,
        "supply_type": "goods",
    }])
    assert rc == 0, err


def test_unrounded_tax_amount_rejected():
    rc, err = run([{
        "tax_key": "19", "net": 100.00, "tax_amount": 19.001,
        "supply_type": "goods",
    }])
    assert rc == 2
    assert "cents" in err.lower() or "§23" in err


def test_kleinbetagsrechnung_einvoice_flag_rejected():
    """A taxed invoice under EUR 250 gross flagged as an e-invoice is wrong:
    it is a Kleinbetagsrechnung and may be a sonstige Rechnung."""
    rc, err = run([{
        "tax_key": "19", "net": 100.00, "tax_amount": 19.00,
        "supply_type": "goods", "e_invoice": True,
    }])
    assert rc == 2
    assert "Kleinbetagsrechnung" in err


def test_oss_on_domestic_supply_not_yet_checked():
    """OSS (§18) is for EU distance sales; claiming it on a domestic supply is
    wrong. The checker has no OSS field yet, so it is accepted — the gap is
    documented in SKILL.md as a known limitation."""
    rc, err = run([{
        "tax_key": "19", "net": 100.00, "tax_amount": 19.00,
        "supply_type": "domestic", "oss": True,
    }])
    assert rc == 0
