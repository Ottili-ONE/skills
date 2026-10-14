"""Tests for webhook_forward.py: SSRF blocking + live delivery to a local server."""
import http.server
import json
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "webhook_forward.py"
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
SCRIPT = SCRIPT_DIR / "webhook_forward.py"


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

    The subprocess cannot be monkeypatched, so the module is loaded
    directly and its two I/O boundaries are faked: resolve_and_check passes
    and urlopen is replaced with a recorder.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("webhook_forward", str(SCRIPT))
    wf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wf)

    captured = {}

    class FakeResp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["data"] = req.data
        captured["method"] = req.get_method()
        return FakeResp()

    monkeypatch.setattr(wf, "resolve_and_check", lambda url, allow_insecure=False: None)
    monkeypatch.setattr(wf.urllib.request, "urlopen", fake_urlopen)
    body = tmp_path / "b.json"; body.write_bytes(b'{"x":1}')
    import sys as _sys
    old_argv = _sys.argv
    _sys.argv = ["webhook_forward.py", "--url", "https://example.com/hook",
                 "--body", str(body)]
    try:
        code = wf.main()
    finally:
        _sys.argv = old_argv
    assert code == 0
    assert captured["data"] == b'{"x":1}'
    assert captured["method"] == "POST"


def test_redirect_not_followed(tmp_path, monkeypatch):
    """urlopen is called exactly once: no automatic redirect following."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("webhook_forward", str(SCRIPT))
    wf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wf)
    calls = []

    class FakeResp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout=None):
        calls.append(req.full_url)
        return FakeResp()

    monkeypatch.setattr(wf, "resolve_and_check", lambda url, allow_insecure=False: None)
    monkeypatch.setattr(wf.urllib.request, "urlopen", fake_urlopen)
    body = tmp_path / "b.json"; body.write_bytes(b'{"x":1}')
    import sys as _sys
    old_argv = _sys.argv
    _sys.argv = ["webhook_forward.py", "--url", "https://example.com/hook",
                 "--body", str(body)]
    try:
        wf.main()
    finally:
        _sys.argv = old_argv
    assert len(calls) == 1
