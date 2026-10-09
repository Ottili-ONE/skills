"""Offline, deterministic tests for the carrier-apis-de scripts."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABEL = ROOT / "scripts" / "label_create.py"
TRACK = ROOT / "scripts" / "track.py"
RECON = ROOT / "scripts" / "reconcile.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True)


def test_label_create_dhl_has_idempotency_header():
    r = run(LABEL, "--carrier", "dhl", "--ref", "ORD-1")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["idempotency_field"] == "X-Request-ID"
    assert data["request"]["headers"]["X-Request-ID"] == "ORD-1"


def test_label_create_ups_uses_body_field():
    r = run(LABEL, "--carrier", "ups", "--ref", "ORD-2")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["idempotency_field"] == "X-Inbound-Idempotency-Key"
    assert data["request"]["headers"]["X-Inbound-Idempotency-Key"] == "ORD-2"


def test_label_create_dpd_embeds_key_in_body():
    r = run(LABEL, "--carrier", "dpd", "--ref", "ORD-3")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["idempotency_field"] == "shipmentReferenceNumber"
    assert "X-Request-ID" not in data["request"]["headers"]
    assert data["request"]["body"]["shipmentReferenceNumber"] == "ORD-3"


def test_label_create_rejects_unknown_carrier():
    r = run(LABEL, "--carrier", "fedex", "--ref", "ORD-4")
    assert r.returncode != 0


def test_track_dry_run_offline():
    r = run(TRACK, "--carrier", "dhl", "--number", "12345678901234567890")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["endpoint_path"].startswith("/shipment/v2/tracking")
    assert data["cache_ttl_seconds"] == 300


def test_reconcile_match():
    label = {"cost": {"amount": 12.50}, "status": "created", "trackingNumber": "T1"}
    record = {"cost": {"amount": 12.50}, "status": "created", "trackingNumber": "T1"}
    lp = Path("/tmp/_lab.json"); lp.write_text(json.dumps(label))
    rp = Path("/tmp/_rec.json"); rp.write_text(json.dumps(record))
    r = run(RECON, "--label", str(lp), "--record", str(rp))
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["ok"] is True


def test_reconcile_mismatch():
    label = {"cost": {"amount": 12.50}, "status": "created", "trackingNumber": "T1"}
    record = {"cost": {"amount": 13.00}, "status": "created", "trackingNumber": "T1"}
    lp = Path("/tmp/_lab2.json"); lp.write_text(json.dumps(label))
    rp = Path("/tmp/_rec2.json"); rp.write_text(json.dumps(record))
    r = run(RECON, "--label", str(lp), "--record", str(rp))
    assert r.returncode == 1, r.stderr
    deltas = json.loads(r.stdout)["deltas"]
    assert any(d["field"] == "cost" for d in deltas)
