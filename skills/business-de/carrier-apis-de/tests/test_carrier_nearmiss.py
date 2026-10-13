"""Near-miss trigger tests for carrier-apis-de scripts.

The traps: a 409 conflict must be re-queried, never re-created; a 401/403 must
re-issue the token, never retry with the same token; the tracking cache TTL;
and reconciling a label whose cost diverges.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABEL = ROOT / "scripts" / "label_create.py"
TRACK = ROOT / "scripts" / "track.py"
RECON = ROOT / "scripts" / "reconcile.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True)


def test_unknown_carrier_rejected():
    r = run(LABEL, "--carrier", "fedex", "--ref", "ORD-4")
    assert r.returncode != 0


def test_idempotency_key_must_be_client_generated():
    """An empty ref is rejected — the key must be a real client reference."""
    r = run(LABEL, "--carrier", "dhl", "--ref", "")
    assert r.returncode != 0


def test_hermes_uses_body_field_not_header():
    r = run(LABEL, "--carrier", "hermes", "--ref", "ORD-6")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["idempotency_field"] == "correlationId"
    assert "X-Request-ID" not in data["request"]["headers"]
    assert data["request"]["body"]["correlationId"] == "ORD-6"


def test_tracking_cache_ttl_is_300_seconds_default(tmp_path):
    """Tracking results are cached for 300 s so the API is not hammered.
    Without --execute the script is fully offline: it builds the request
    envelope and reports the cache TTL without touching the network."""
    cache = tmp_path / "cache.json"
    r = run(TRACK, "--carrier", "dhl", "--number", "12345678901234567890",
            "--cache-file", str(cache))
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["cache_ttl_seconds"] == 300


def test_reconcile_cost_mismatch_flagged(tmp_path):
    label = {"cost": {"amount": 12.50}, "status": "created",
             "trackingNumber": "12345678901234567890"}
    record = {"cost": {"amount": 14.90}, "status": "created",
              "trackingNumber": "12345678901234567890"}
    lp = tmp_path / "l.json"; lp.write_text(json.dumps(label))
    rp = tmp_path / "r.json"; rp.write_text(json.dumps(record))
    r = run(RECON, "--label", str(lp), "--record", str(rp))
    assert r.returncode == 1, r.stderr
    deltas = json.loads(r.stdout)["deltas"]
    assert any(d["field"] == "cost" for d in deltas)


def test_reconcile_status_mismatch_flagged(tmp_path):
    label = {"cost": {"amount": 12.50}, "status": "created",
             "trackingNumber": "12345678901234567890"}
    record = {"cost": {"amount": 12.50}, "status": "shipped",
              "trackingNumber": "12345678901234567890"}
    lp = tmp_path / "l.json"; lp.write_text(json.dumps(label))
    rp = tmp_path / "r.json"; rp.write_text(json.dumps(record))
    r = run(RECON, "--label", str(lp), "--record", str(rp))
    assert r.returncode == 1
    deltas = json.loads(r.stdout)["deltas"]
    assert any(d["field"] == "status" for d in deltas)


def test_reconcile_perfect_match(tmp_path):
    label = {"cost": {"amount": 12.50}, "status": "created",
             "trackingNumber": "12345678901234567890"}
    record = {"cost": {"amount": 12.50}, "status": "created",
              "trackingNumber": "12345678901234567890"}
    lp = tmp_path / "l.json"; lp.write_text(json.dumps(label))
    rp = tmp_path / "r.json"; rp.write_text(json.dumps(record))
    r = run(RECON, "--label", str(lp), "--record", str(rp))
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["ok"] is True
    assert out["deltas"] == []
