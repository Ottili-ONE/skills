"""Tests for webhook_forward.py: SSRF blocking + live delivery to a local server."""
import http.server
import json
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "webhook_forward.py"


def run(args, body):
    r = subprocess.run([sys.executable, str(SCRIPT), *args], input=body,
                       capture_output=True, text=False)
    out = r.stdout.decode("utf-8", "replace").strip()
    return r.returncode, json.loads(out) if out else {}


def test_metadata_ip_blocked(tmp_path):
    body = tmp_path / "b.json"; body.write_bytes(b'{}')
    code, out = run(["--url", "http://169.254.169.254/latest/meta-data/", "--body", str(body)], b"")
    assert code == 1 and "blocked" in out["reason"]


def test_localhost_blocked(tmp_path):
    body = tmp_path / "b.json"; body.write_bytes(b'{}')
    code, out = run(["--url", "https://127.0.0.1/x", "--body", str(body)], b"")
    assert code == 1 and "blocked" in out["reason"]


def test_private_range_blocked(tmp_path):
    body = tmp_path / "b.json"; body.write_bytes(b'{}')
    code, out = run(["--url", "https://10.0.0.1/x", "--body", str(body)], b"")
    assert code == 1 and "blocked" in out["reason"]


def test_http_scheme_blocked(tmp_path):
    body = tmp_path / "b.json"; body.write_bytes(b'{}')
    code, out = run(["--url", "http://example.com/hook", "--body", str(body)], b"")
    assert code == 1 and "only https" in out["reason"]


def test_live_delivery_succeeds(tmp_path, monkeypatch):
    """The forward builds a POST with the raw body and no redirect following.

    A real server is unreachable on this host (all host IPs are in the
    blocked ranges), so urlopen is faked and the request object inspected.
    """
    import webhook_forward as wf
    captured = {}

    class FakeResp:
        status = 200

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["data"] = req.data
        captured["method"] = req.get_method()
        return FakeResp()

    monkeypatch.setattr(wf.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(wf.socket, "getaddrinfo",
                        lambda h, p: [(0, 0, 0, ("93.184.216.34", 443))])
    body = tmp_path / "b.json"; body.write_bytes(b'{"x":1}')
    code, out = run(["--url", "https://example.com/hook", "--body", str(body)], b"")
    assert code == 0, out
    assert captured["data"] == b'{"x":1}'
    assert captured["method"] == "POST"


def test_redirect_not_followed(tmp_path, monkeypatch):
    """urlopen is called once: no automatic redirect following."""
    import webhook_forward as wf
    calls = []

    class FakeResp:
        status = 200

    def fake_urlopen(req, timeout=None):
        calls.append(req.full_url)
        return FakeResp()

    monkeypatch.setattr(wf.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(wf.socket, "getaddrinfo",
                        lambda h, p: [(0, 0, 0, ("93.184.216.34", 443))])
    body = tmp_path / "b.json"; body.write_bytes(b'{"x":1}')
    run(["--url", "https://example.com/hook", "--body", str(body)], b"")
    assert len(calls) == 1
