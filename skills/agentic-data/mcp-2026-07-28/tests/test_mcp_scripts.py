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


# --- error-code mapping (added in PASS 2 / EXPAND) ---

def test_error_code_range_resolved():
    """The 2026-07-28 reserved range is -32020..-32099; old codes map over."""
    old_to_new = {"-32001": "-32020", "-32003": "-32021", "-32004": "-32022"}
    assert old_to_new["-32001"] == "-32020"  # HeaderMismatch
    assert old_to_new["-32003"] == "-32021"  # MissingRequiredClientCapability
    assert old_to_new["-32004"] == "-32022"  # UnsupportedProtocolVersion


def test_protocol_check_strict_promotes_info_to_fail():
    doc = json.dumps({"result": {
        "supportedVersions": ["2025-11-25"],
        "capabilities": {},
        "serverInfo": {"name": "demo", "version": "1.0"},
    }})
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py"), "--strict"],
        input=doc, capture_output=True, text=True)
    assert r.returncode == 1
    assert "FAIL" in r.stderr


def test_protocol_check_rejects_error_envelope():
    doc = json.dumps({"error": {"code": -32601, "message": "nope"}})
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py")],
        input=doc, capture_output=True, text=True)
    assert r.returncode == 1
    assert "error" in r.stderr.lower()


def test_protocol_check_rejects_non_object():
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py")],
        input='[1, 2, 3]', capture_output=True, text=True)
    assert r.returncode == 1
    assert "object" in r.stderr.lower()


def test_protocol_check_missing_file_returns_2():
    r = run("protocol_check.py", "/nonexistent/path/xyz.json")
    assert r.returncode == 2


def test_protocol_check_directory_returns_2():
    import tempfile
    d = tempfile.mkdtemp()
    r = run("protocol_check.py", d)
    assert r.returncode == 2


def test_stateless_probe_flags_differring_meta():
    a = json.dumps({"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"},
                    "result": {"x": 1}})
    b = json.dumps({"_meta": {"io.modelcontextprotocol/protocolVersion": "2025-11-25"},
                    "result": {"x": 1}})
    p1, p2 = _write(a), _write(b)
    r = run("stateless_probe.py", p1, p2)
    assert r.returncode == 1
    assert "_meta" in r.stderr.lower()


def test_stateless_probe_flags_missing_protocol_version():
    a = json.dumps({"_meta": {}, "result": {"x": 1}})
    p1, p2 = _write(a), _write(a)
    r = run("stateless_probe.py", p1, p2)
    assert r.returncode == 1
    assert "protocolVersion" in r.stderr


def test_stateless_probe_flags_different_results():
    a = json.dumps({"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"},
                    "result": {"x": 1}})
    b = json.dumps({"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"},
                    "result": {"x": 2}})
    p1, p2 = _write(a), _write(b)
    r = run("stateless_probe.py", p1, p2)
    assert r.returncode == 1
    assert "results differ" in r.stderr.lower()


def test_version_negotiate_unknown_version_is_ignored():
    """An unknown revision is not in ALLOWED, so it cannot drive agreement."""
    r = run("version_negotiate.py", "--client", "2099-01-01",
            "--server", "2026-07-28")
    assert r.returncode == 1
    assert "0 1 0" in r.stdout


def test_version_negotiate_picks_highest_common():
    r = run("version_negotiate.py", "--client", "2026-07-28,2025-06-18,2025-11-25",
            "--server", "2025-11-25,2025-06-18")
    assert r.returncode == 0
    assert "agreed 2025-11-25" in r.stderr


# --- tasks extension coverage (added in PASS 3 / TEST+FIX) ---

def test_protocol_check_tasks_extension_present():
    doc = json.dumps({"result": {
        "supportedVersions": ["2026-07-28"],
        "capabilities": {"tasks": {"extensions": ["io.modelcontextprotocol/tasks"]}},
        "serverInfo": {"name": "demo", "version": "1.0"},
    }})
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py")],
        input=doc, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_protocol_check_rejects_tasks_result_method():
    """tasks/result was removed in 2026-07-28; a server still advertising it is stale."""
    doc = json.dumps({"result": {
        "supportedVersions": ["2026-07-28"],
        "capabilities": {"tasks": {"methods": ["tasks/result"]}},
        "serverInfo": {"name": "demo", "version": "1.0"},
    }})
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py")],
        input=doc, capture_output=True, text=True)
    assert "tasks/result" in r.stderr


def test_protocol_check_strict_promotes_unknown_version():
    doc = json.dumps({"result": {
        "supportedVersions": ["2099-01-01"],
        "capabilities": {},
        "serverInfo": {"name": "demo", "version": "1.0"},
    }})
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py"), "--strict"],
        input=doc, capture_output=True, text=True)
    assert r.returncode == 1
    assert "FAIL" in r.stderr


def test_version_negotiate_picks_highest_common_from_unsorted():
    r = run("version_negotiate.py", "--client", "2026-07-28,2025-06-18",
            "--server", "2025-11-25,2025-06-18")
    assert r.returncode == 0, r.stderr
    assert "agreed 2025-06-18" in r.stderr  # highest common, not 2025-11-25


def test_stateless_probe_flags_session_envelope():
    pair = json.dumps({
        "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
                  "session": "abc"},
        "result": {"x": 1},
    })
    p1, p2 = _write(pair), _write(pair)
    r = run("stateless_probe.py", p1, p2)
    assert r.returncode == 1
    assert "session" in r.stderr.lower()


def test_stateless_probe_flags_differing_results():
    a = json.dumps({"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"},
                    "result": {"x": 1}})
    b = json.dumps({"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"},
                    "result": {"x": 2}})
    p1, p2 = _write(a), _write(b)
    r = run("stateless_probe.py", p1, p2)
    assert r.returncode == 1
    assert "differ" in r.stderr.lower() or "result" in r.stderr.lower()


# --- hardened script behaviour (added in EXPAND pass) ---

def test_version_negotiate_json_mode_agrees():
    r = run("version_negotiate.py", "--client", "2026-07-28",
            "--server", "2026-07-28", "--json")
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out == {"agreed": "2026-07-28", "refused": None}


def test_version_negotiate_json_mode_refuses():
    r = run("version_negotiate.py", "--client", "2025-06-18",
            "--server", "2026-07-28", "--json")
    assert r.returncode == 1
    out = json.loads(r.stdout)
    assert out == {"agreed": None, "refused": "-32022"}


def test_version_negotiate_drops_unknown_revision():
    """An unknown revision cannot drive agreement; it is reported and ignored."""
    r = run("version_negotiate.py", "--client", "2099-01-01,2026-07-28",
            "--server", "2026-07-28")
    assert r.returncode == 0
    assert "unknown" in r.stderr.lower()
    assert "agreed 2026-07-28" in r.stderr


def test_version_negotiate_dedupes_duplicates():
    r = run("version_negotiate.py", "--client", "2026-07-28,2026-07-28",
            "--server", "2026-07-28,2026-07-28")
    assert r.returncode == 0
    assert "agreed 2026-07-28" in r.stderr


def test_protocol_check_json_mode():
    doc = json.dumps({"result": {
        "supportedVersions": ["2026-07-28"],
        "capabilities": {},
        "serverInfo": {"name": "demo", "version": "1.0"},
    }})
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py"), "--json"],
        input=doc, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["valid"] is True
    assert out["fails"] == 0


def test_protocol_check_json_mode_invalid():
    doc = json.dumps({"result": {"supportedVersions": ["2026-07-28"]}})
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py"), "--json"],
        input=doc, capture_output=True, text=True)
    assert r.returncode == 1
    out = json.loads(r.stdout)
    assert out["valid"] is False
    assert out["fails"] >= 1


def test_protocol_check_rejects_empty_input():
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py")],
        input="", capture_output=True, text=True)
    assert r.returncode == 2
    assert "empty" in r.stderr.lower()


def test_protocol_check_rejects_invalid_json():
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py")],
        input="not json at all", capture_output=True, text=True)
    assert r.returncode == 2
    assert "json" in r.stderr.lower()


def test_protocol_check_warns_on_duplicate_versions():
    doc = json.dumps({"result": {
        "supportedVersions": ["2026-07-28", "2026-07-28"],
        "capabilities": {},
        "serverInfo": {"name": "demo", "version": "1.0"},
    }})
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "protocol_check.py")],
        input=doc, capture_output=True, text=True)
    assert r.returncode == 0
    assert "duplicate" in r.stderr.lower()


# --- reference coverage (added in EXPAND pass) ---

def test_reference_files_exist_and_are_substantive():
    refs = Path(__file__).resolve().parent.parent / "references"
    for name in ("server-discover.md", "meta-schema.md", "tasks-extension.md"):
        p = refs / name
        assert p.is_file(), f"missing reference {name}"
        body = p.read_text(encoding="utf-8")
        assert len(body.splitlines()) >= 25, f"{name} is too thin ({len(body.splitlines())} lines)"


def test_reference_links_resolve():
    """SKILL.md links one level deep into references/ and every target exists."""
    root = Path(__file__).resolve().parent.parent
    body = (root / "SKILL.md").read_text(encoding="utf-8")
    import re as _re
    for raw in _re.findall(r"`?references/([^`\s]+\.md)`?", body):
        target = (root / "references" / raw.strip()).resolve()
        assert target.is_file(), f"dangling reference link {raw!r}"
        target.relative_to((root / "references").resolve())


# --- hardened stateless_probe edge cases (EXPAND pass 2) ---

def _w(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_stateless_probe_rejects_non_object(tmp_path):
    a = _w(tmp_path, "a.json", json.dumps(["not", "an", "object"]))
    b = _w(tmp_path, "b.json", json.dumps({"_meta": {}, "result": {}}))
    r = run("stateless_probe.py", a, b)
    assert r.returncode == 1
    assert "object" in r.stderr.lower()


def test_stateless_probe_flags_empty_meta(tmp_path):
    a = _w(tmp_path, "a.json", json.dumps({"_meta": {}, "result": {"x": 1}}))
    b = _w(tmp_path, "b.json", json.dumps({"_meta": {}, "result": {"x": 1}}))
    r = run("stateless_probe.py", a, b)
    assert r.returncode == 1
    assert "empty" in r.stderr.lower()


def test_stateless_probe_accepts_valid_replay(tmp_path):
    a = _w(tmp_path, "a.json", json.dumps({
        "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"},
        "result": {"x": 1}}))
    b = _w(tmp_path, "b.json", json.dumps({
        "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"},
        "result": {"x": 1}}))
    r = run("stateless_probe.py", a, b)
    assert r.returncode == 0, r.stderr
    assert "1 0 0" in r.stdout


def test_stateless_probe_flags_meta_without_protocolversion(tmp_path):
    a = _w(tmp_path, "a.json", json.dumps({
        "_meta": {"io.modelcontextprotocol/clientInfo": {"name": "x"}},
        "result": {"x": 1}}))
    b = _w(tmp_path, "b.json", json.dumps({
        "_meta": {"io.modelcontextprotocol/clientInfo": {"name": "x"}},
        "result": {"x": 1}}))
    r = run("stateless_probe.py", a, b)
    assert r.returncode == 1
    assert "protocolVersion" in r.stderr
