import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True,
    )


def test_version_negotiate_agrees():
    r = run("version_negotiate.py", "--client", "2026-07-28,2025-06-18",
            "--server", "2026-07-28,2025-06-18")
    assert r.returncode == 0, r.stderr
    assert "agreed 2026-07-28" in r.stderr


def test_version_negotiate_refuses_no_overlap():
    r = run("version_negotiate.py", "--client", "2025-06-18", "--server", "2026-07-28")
    assert r.returncode == 1
    assert "0 1 0" in r.stdout
    assert "-32022" in r.stderr


def test_protocol_check_valid_discover():
    doc = json.dumps({"result": {
        "supportedVersions": ["2026-07-28"],
        "capabilities": {},
        "serverInfo": {"name": "demo", "version": "1.0"},
    }})
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py")],
        input=doc, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "3 0 0" in r.stdout


def test_protocol_check_missing_fields():
    doc = json.dumps({"result": {"supportedVersions": ["2026-07-28"]}})
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py")],
        input=doc, capture_output=True, text=True)
    assert r.returncode == 1
    assert "FAIL" in r.stderr


def _write(payload):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    f.write(payload)
    f.close()
    return f.name


def test_stateless_probe_passes():
    pair = json.dumps({
        "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"},
        "result": {"x": 1},
    })
    p1, p2 = _write(pair), _write(pair)
    r = run("stateless_probe.py", p1, p2)
    assert r.returncode == 0, r.stderr
    assert "1 0 0" in r.stdout


def test_stateless_probe_flags_session():
    bad = json.dumps({
        "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
                  "session": "abc"},
        "result": {},
    })
    p1, p2 = _write(bad), _write(bad)
    r = run("stateless_probe.py", p1, p2)
    assert r.returncode == 1
    assert "session" in r.stderr.lower()
