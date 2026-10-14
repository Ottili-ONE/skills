"""Tests for carrier-apis-de scripts: idempotency key, charge reconciliation, tracking validation."""
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def run(script, args, stdin=None):
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                       input=stdin, capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout) if r.stdout.strip() else {}


def test_create_label_injects_idempotency_key(tmp_path):
    order = tmp_path / "o.json"; order.write_text('{"sender": {"name": "A"}}')
    out = tmp_path / "label.pdf"
    code, out_ = run("create_label.py", ["--provider", "dhl", "--order", str(order),
                                         "--client-ref", "ship_001", "--out", str(out)])
    assert code == 0
    assert out_["client_reference_no"] == "ship_001"
    assert out_["payload"]["clientReferenceNo"] == "ship_001"
    assert out.exists()


def test_reconcile_matched(tmp_path):
    charges = tmp_path / "c.csv"
    charges.write_text("reference,amount\nship_001,10.00\nship_002,12.00\n")
    ledger = tmp_path / "l.json"
    ledger.write_text(json.dumps([{"reference": "ship_001"}, {"reference": "ship_002"}]))
    code, out = run("reconcile_charges.py", ["--charges", str(charges), "--ledger", str(ledger)])
    assert code == 0 and out["matched"] == 2 and out["unknown"] == []


def test_reconcile_unknown(tmp_path):
    charges = tmp_path / "c.csv"
    charges.write_text("reference,amount\nship_001,10.00\nship_ghost,99.00\n")
    ledger = tmp_path / "l.json"
    ledger.write_text(json.dumps([{"reference": "ship_001"}]))
    code, out = run("reconcile_charges.py", ["--charges", str(charges), "--ledger", str(ledger)])
    assert code == 1
    assert out["unknown"][0]["reference"] == "ship_ghost"


def test_track_invalid_ekp():
    code, out = run("track_shipment.py", ["--provider", "dhl", "--ekp", "X", "--tracking", "1"])
    assert code == 1 and out["reason"] == "invalid_ekp"


def test_track_valid_dry_run():
    code, out = run("track_shipment.py", ["--provider", "dhl", "--ekp", "DE001234567890",
                                          "--tracking", "123456789012"])
    assert code == 0 and out["ok"] is True
