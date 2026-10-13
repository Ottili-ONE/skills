"""Near-miss trigger tests for webhooks-safe scripts.

The traps: a stale Stripe signature outside the 5-minute replay window, a
raw-body re-encoding that breaks the HMAC, an SSRF attempt at a private IP,
and a dead-letter entry that has exhausted its retries.
"""
import hashlib
import hmac
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "scripts" / "verify.py"
DEDUPE = ROOT / "scripts" / "dedupe.py"
DEADLETTER = ROOT / "scripts" / "deadletter.py"
ORDER = ROOT / "scripts" / "ordering.py"
SSRF = ROOT / "scripts" / "ssrf_check.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True)


def _body(content):
    p = Path(tempfile.mkdtemp()) / "body.json"
    p.write_bytes(content)
    return p


def test_stale_stripe_signature_rejected():
    """Stripe's 5-minute replay window: a signature older than 5 minutes is
    rejected even if the HMAC is otherwise correct."""
    body = b'{"type":"payment_intent.succeeded"}'
    ts = 1700000000  # long ago
    sig = f"t={ts},v1=" + hmac.new(b"secret", f"{ts}.".encode() + body,
                                   hashlib.sha256).hexdigest()
    r = run(VERIFY, "--provider", "stripe", "--secret", "secret",
            "--body", str(_body(body)), "--sig", sig, "--now", "1700000999")
    assert r.returncode == 1
    assert json.loads(r.stdout)["valid"] is False


def test_stripe_signature_within_window_accepted():
    body = b'{"type":"payment_intent.succeeded"}'
    ts = 1700000000
    sig = f"t={ts},v1=" + hmac.new(b"secret", f"{ts}.".encode() + body,
                                   hashlib.sha256).hexdigest()
    r = run(VERIFY, "--provider", "stripe", "--secret", "secret",
            "--body", str(_body(body)), "--sig", sig, "--now", "1700000200")
    assert r.returncode == 0


def test_reencoding_body_breaks_signature():
    """Re-encoding the parsed JSON changes byte order and breaks the HMAC.
    The skill verifies over the RAW bytes."""
    body = b'{"a": 1, "b": 2}'
    sig = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    # an agent that re-serialises the parsed body must fail verification
    reencoded = json.dumps(json.loads(body)).encode()
    r = run(VERIFY, "--provider", "github", "--secret", "secret",
            "--body", str(_body(reencoded)), "--sig", sig)
    assert r.returncode == 1


def test_ssrf_private_ip_rejected():
    r = run(SSRF, "--url", "http://169.254.169.254/latest/meta-data/",
            "--allow", "ottili.example")
    assert r.returncode == 1
    out = json.loads(r.stdout)
    assert out["ok"] is False
    assert "not in allow-list" in out["reason"] or "IP" in out["reason"]


def test_ssrf_loopback_rejected():
    r = run(SSRF, "--url", "http://127.0.0.1/admin", "--allow", "ottili.example")
    assert r.returncode == 1


def test_ssrf_allow_list_subdomain_accepted():
    r = run(SSRF, "--url", "https://api.ottili.example/webhooks/inbound",
            "--allow", "ottili.example")
    assert r.returncode == 0
    assert json.loads(r.stdout)["ok"] is True


def test_ssrf_disallowed_host_rejected():
    r = run(SSRF, "--url", "https://evil.example/exfil",
            "--allow", "ottili.example")
    assert r.returncode == 1


def test_dedupe_blocks_second_delivery():
    """A second delivery with the same event id is a duplicate."""
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "events.jsonl"
        r1 = run(DEDUPE, "--event-id", "del-1", "--store", str(state))
        assert r1.returncode == 0
        assert json.loads(r1.stdout)["duplicate"] is False
        r2 = run(DEDUPE, "--event-id", "del-1", "--store", str(state))
        assert r2.returncode == 0
        assert json.loads(r2.stdout)["duplicate"] is True


def test_deadletter_records_failure_reason():
    """A failed webhook is never silently dropped — it goes to the dead-letter
    queue with the raw payload, the reason and a timestamp."""
    with tempfile.TemporaryDirectory() as d:
        payload = Path(d) / "body.json"
        payload.write_bytes(b'{"type":"x"}')
        queue = Path(d) / "dl.jsonl"
        r = run(DEADLETTER, "--event-id", "del-9", "--reason", "timeout",
                "--payload", str(payload), "--queue", str(queue))
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert out["queued"] == str(queue)
        rec = json.loads(queue.read_text().splitlines()[0])
        assert rec["event_id"] == "del-9"
        assert rec["reason"] == "timeout"
        assert rec["payload"] == '{"type":"x"}'
        assert "timestamp" in rec


def test_ordering_gap_hold():
    """A sequence gap (1, 2, 4) is held until the missing event arrives."""
    with tempfile.TemporaryDirectory() as d:
        state = Path(d) / "state.json"
        payload = Path(d) / "body.json"
        payload.write_bytes(b'{"seq":1}')
        run(ORDER, "--stream", "s1", "--seq", "1", "--payload", str(payload),
            "--store", str(state))
        run(ORDER, "--stream", "s1", "--seq", "2", "--payload", str(payload),
            "--store", str(state))
        r = run(ORDER, "--stream", "s1", "--seq", "4", "--payload", str(payload),
                "--store", str(state))
        assert r.returncode == 1  # hold is not "handled"
        out = json.loads(r.stdout)
        assert out["action"] == "hold"
        assert out["held_count"] >= 1
        # when seq 3 arrives, 4 is released from the held set
        r2 = run(ORDER, "--stream", "s1", "--seq", "3", "--payload", str(payload),
                 "--store", str(state))
        out2 = json.loads(r2.stdout)
        assert out2["action"] == "process"
        assert any(h["seq"] == 4 for h in out2.get("released", []))
