"""Tests for scripts/handoff.py — run with pytest or plain python3 -m pytest."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "handoff.py"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import handoff  # noqa: E402


def run(args, stdin=None):
    p = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin, capture_output=True, text=True,
    )
    return p.returncode, p.stdout, p.stderr


def test_build_returns_dict_not_none_on_mismatch():
    """build() must never return None: callers pass it straight to validate(),
    which crashes on NoneType."""
    class A: pass
    a = A()
    a.task = "t"; a.url = "http://x"; a.title = "T"
    a.field = ["heading=Hi"]; a.locator = []; a.out = None; a.validate = None
    s = handoff.build(a)
    assert isinstance(s, dict), f"build() returned {type(s).__name__}, not a dict"
    assert s.get("_error")
    # validate() must tolerate it, not crash
    errs = handoff.validate(s)
    assert errs and "build failed" in errs[0]


def test_validate_tolerates_none():
    """validate(None) returns an error list, it does not raise."""
    errs = handoff.validate(None)
    assert errs and "None" in errs[0]


def test_build_and_validate_round_trip(tmp_path):
    out = tmp_path / "s.json"
    rc, _, err = run([
        "--task", "scrape", "--url", "https://x", "--title", "T",
        "--field", "headline=Hi", "--locator",
        "page.getByRole('heading', { level: 1 }).first()",
        "--out", str(out),
    ])
    assert rc == 0, err
    assert out.is_file()
    data = json.loads(out.read_text())
    assert data["context_closed"] is True
    assert data["locator_strings"][0].startswith("page.getByRole")
    assert data["evidence"][0]["field"] == "headline"
    assert data["evidence"][0]["locator"].startswith("page.getByRole")
    # round-trip: the written file must validate
    rc2, _, err2 = run(["--validate", str(out)])
    assert rc2 == 0, err2


def test_validate_rejects_missing_required(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({"task": "t"}))
    rc, _, err = run(["--validate", str(f)])
    assert rc == 1
    assert "missing required field" in err


def test_validate_rejects_context_not_closed(tmp_path):
    f = tmp_path / "open.json"
    f.write_text(json.dumps({
        "task": "t", "url": "u", "title": "T",
        "ended_at": "2026-10-12T00:00:00Z",
        "locator_strings": ["x"], "key_fields": {"a": "b"},
        "evidence": [{"field": "a", "value": "b", "locator": "x"}],
        "flags": [], "context_closed": False,
    }))
    rc, _, err = run(["--validate", str(f)])
    assert rc == 1
    assert "context_closed" in err


def test_validate_rejects_empty_locator_strings(tmp_path):
    f = tmp_path / "noloc.json"
    f.write_text(json.dumps({
        "task": "t", "url": "u", "title": "T",
        "ended_at": "2026-10-12T00:00:00Z",
        "locator_strings": [], "key_fields": {},
        "evidence": [], "flags": [], "context_closed": True,
    }))
    rc, _, err = run(["--validate", str(f)])
    assert rc == 1
    assert "locator_strings" in err


def test_validate_rejects_evidence_without_locator(tmp_path):
    f = tmp_path / "noevloc.json"
    f.write_text(json.dumps({
        "task": "t", "url": "u", "title": "T",
        "ended_at": "2026-10-12T00:00:00Z",
        "locator_strings": ["x"], "key_fields": {"a": "b"},
        "evidence": [{"field": "a", "value": "b", "locator": ""}],
        "flags": [], "context_closed": True,
    }))
    rc, _, err = run(["--validate", str(f)])
    assert rc == 1
    assert "missing locator" in err


def test_validate_rejects_unreadable_file():
    rc, _, err = run(["--validate", "/nonexistent/handoff.json"])
    assert rc == 1
    assert "cannot read" in err
