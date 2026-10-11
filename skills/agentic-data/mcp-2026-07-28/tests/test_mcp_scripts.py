import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def run(script, *args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        input=stdin, capture_output=True, text=True,
    )

# helper alias used by the stateless-probe tests
def run_stdin(script, payload):
    return run(script, stdin=payload)


def test_version_negotiate_agrees():
    r = run("version_negotiate.py", "--client", "2026-07-28,2025-06-18", "--server", "2026-07-28,2025-06-18")
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
    r = run("protocol_check.py", stdin=doc)
    assert r.returncode == 0, r.stderr
    assert "3 0 0" in r.stdout


def test_protocol_check_missing_fields():
    doc = json.dumps({"result": {"supportedVersions": ["2026-07-28"]}})
    r = run("protocol_check.py", stdin=doc)
    assert r.returncode == 1
    assert "FAIL" in r.stderr


def test_stateless_probe_passes():
    import tempfile
    pair = json.dumps({
        "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"},
        "result": {"x": 1},
    })
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write(pair)
        p1 = f.name
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write(pair)
        p2 = f.name
    r = run("stateless_probe.py", p1, p2)
    assert r.returncode == 0, r.stderr
    assert "1 0 0" in r.stdout


def test_stateless_probe_flags_session():
    import tempfile
    bad = json.dumps({"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "session": "abc"}, "result": {}})
    paths = []
    for _ in range(2):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write(bad)
            paths.append(f.name)
    r = run("stateless_probe.py", *paths)
    assert r.returncode == 1
    assert "session" in r.stderr.lower() or "SESSION" in r.stderr
