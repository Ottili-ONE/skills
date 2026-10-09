"""Offline, deterministic tests for the webhooks-safe scripts."""
import hashlib
import hmac
import json
import subprocess
import sys
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


def _body_file(content):
    p = Path("/tmp/_wh_body.json")
    p.write_bytes(content)
    return p


def test_verify_github_valid():
    body = b'{"action":"opened"}'
    sig = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    r = run(VERIFY, "--provider", "github", "--secret", "secret",
            "--body", str(_body_file(body)), "--sig", sig)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["valid"] is True


def test_verify_github_rejects_bad_sig():
    body = b'{"action":"opened"}'
    r = run(VERIFY, "--provider", "github", "--secret", "secret",
            "--body", str(_body_file(body)), "--sig", "sha256=deadbeef")
    assert r.returncode != 0
    assert json.loads(r.stdout)["valid"] is False


def test_verify_stripe_replay_rejected():
    body = b'{"id":"evt_1"}'
    old_ts = 1
    sig = f"t={old_ts},v1=" + hmac.new(b"secret", f"{old_ts}.".encode() + body, hashlib.sha256).hexdigest()
    r = run(VERIFY, "--provider", "stripe", "--secret", "secret",
            "--body", str(_body_file(body)), "--sig", sig, "--now", "1000000")
    assert r.returncode != 0  # outside the 5-minute replay window


def test_dedupe_first_and_second():
    store = Path("/tmp/_dedupe_test.jsonl")
    store.unlink(missing_ok=True)
    r1 = run(DEDUPE, "--event-id", "evt-1", "--ttl", "3600", "--store", str(store))
    assert r1.returncode == 0
    assert json.loads(r1.stdout)["duplicate"] is False
    r2 = run(DEDUPE, "--event-id", "evt-1", "--ttl", "3600", "--store", str(store))
    assert r2.returncode == 0
    assert json.loads(r2.stdout)["duplicate"] is True


def test_deadletter_writes_record():
    payload = Path("/tmp/_dl_payload.json")
    payload.write_text('{"id": "x"}')
    q = Path("/tmp/_dl_queue.jsonl")
    q.unlink(missing_ok=True)
    r = run(DEADLETTER, "--event-id", "evt-9", "--reason", "timeout",
            "--payload", str(payload), "--queue", str(q))
    assert r.returncode == 0, r.stderr
    rec = json.loads(q.read_text().splitlines()[0])
    assert rec["event_id"] == "evt-9" and rec["reason"] == "timeout"
    assert rec["payload"] == '{"id": "x"}'


def test_ordering_in_order():
    import tempfile, os
    store = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    store.write("{}"); store.close()
    r = run(ORDER, "--stream", "github:ottili", "--seq", "1",
            "--payload", str(_body_file(b"{\"x\":1}")), "--store", store.name)
    os.unlink(store.name)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["action"] == "process"


def test_ordering_out_of_order_is_held():
    import tempfile, os
    store = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    store.write('{"last_seq": 0, "held": {}}'); store.close()
    r = run(ORDER, "--stream", "github:ottili", "--seq", "3",
            "--payload", str(_body_file(b"{\"x\":1}")), "--store", store.name)
    os.unlink(store.name)
    assert r.returncode == 1, r.stderr
    assert json.loads(r.stdout)["action"] == "hold"


def test_ordering_old_seq_skipped():
    import tempfile, os
    store = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    store.write('{"last_seq": 5, "held": {}}'); store.close()
    r = run(ORDER, "--stream", "github:ottili", "--seq", "3",
            "--payload", str(_body_file(b"{\"x\":1}")), "--store", store.name)
    os.unlink(store.name)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["action"] == "duplicate_or_old"


def test_ssrf_allows_allowed_host():
    r = run(SSRF, "--url", "https://ottili.example/webhooks/inbound",
            "--allow", "ottili.example")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["ok"] is True


def test_ssrf_rejects_other_host():
    r = run(SSRF, "--url", "https://evil.example/x",
            "--allow", "ottili.example")
    assert r.returncode == 1, r.stderr
    assert json.loads(r.stdout)["ok"] is False


def test_ssrf_rejects_loopback():
    r = run(SSRF, "--url", "http://127.0.0.1/admin",
            "--allow", "ottili.example")
    assert r.returncode == 1, r.stderr
    assert "loopback" in json.loads(r.stdout)["reason"]


def test_ssrf_rejects_ip_literal():
    r = run(SSRF, "--url", "https://1.2.3.4/x",
            "--allow", "ottili.example")
    assert r.returncode == 1, r.stderr
    assert json.loads(r.stdout)["ok"] is False
