"""Tests for verify_webhook.py: constant-time compare, provider schemes, stale ts."""
import hashlib
import hmac
import json
import subprocess
import sys
import time
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "verify_webhook.py"
CONFIG = Path(__file__).resolve().parent.parent.parent.parent / "business-de" / "config" / "versions.json"


def run(args, body=b""):
    r = subprocess.run([sys.executable, str(SCRIPT), *args, "--config", str(CONFIG)],
                       input=body, capture_output=True, text=False)
    out = r.stdout.decode("utf-8", "replace").strip()
    return r.returncode, json.loads(out) if out else {}


def test_github_valid():
    body = b'{"action":"opened"}'
    mac = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    code, out = run(["--provider", "github", "--secret", "secret",
                     "--header", f"X-Hub-Signature-256: sha256={mac}"], body)
    assert code == 0, out
    assert out["ok"] is True


def test_github_wrong_signature_rejected():
    body = b'{"action":"opened"}'
    code, out = run(["--provider", "github", "--secret", "secret",
                     "--header", "X-Hub-Signature-256: sha256=deadbeef"], body)
    assert code == 1
    assert out["ok"] is False


def test_compare_digest_not_string_eq():
    """The script must use hmac.compare_digest, not ==."""
    src = SCRIPT.read_text()
    assert "compare_digest" in src
    assert "==" not in src.split("compare_digest")[0].rsplit("\n", 1)[0][-200:]


def test_stripe_valid():
    body = b'{"type":"charge.succeeded"}'
    ts = str(int(time.time()))
    mac = hmac.new(b"sk", f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    code, out = run(["--provider", "stripe", "--secret", "sk",
                     "--header", f"X-Signature: t={ts},v1={mac}"], body)
    assert code == 0, out


def test_stale_timestamp_rejected():
    body = b'{"type":"charge.succeeded"}'
    ts = str(int(time.time()) - 600)  # 10 min ago, outside 5-min window
    mac = hmac.new(b"sk", f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    code, out = run(["--provider", "stripe", "--secret", "sk",
                     "--header", f"X-Signature: t={ts},v1={mac}"], body)
    assert code == 1
    assert out["reason"] == "stale_timestamp"


def test_malformed_header():
    code, out = run(["--provider", "stripe", "--secret", "sk",
                     "--header", "X-Signature: garbage"], b"{}")
    assert code == 1
    assert out["reason"] == "malformed_header"
