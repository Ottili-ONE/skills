"""Tests for publish-reconcile-wp-meta scripts: payload shape + ledger reconciliation."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def run(script, args):
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                       capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout) if r.stdout.strip() else {}


def test_publish_valid(tmp_path):
    content = tmp_path / "post.json"
    content.write_text(json.dumps({
        "client_reference": "cp_001", "title": "T", "body": "B", "status": "publish"}))
    code, out = run("publish_post.py", ["--content", str(content), "--providers", "wp,meta"])
    assert code == 0
    assert out["providers"]["wp"]["method"] == "POST"
    assert out["providers"]["meta"]["url"].endswith("/feed")


def test_publish_missing_field(tmp_path):
    content = tmp_path / "post.json"
    content.write_text(json.dumps({"title": "T", "body": "B", "status": "publish"}))
    code, out = run("publish_post.py", ["--content", str(content)])
    assert code == 1 and out["ok"] is False


def test_publish_invalid_status(tmp_path):
    content = tmp_path / "post.json"
    content.write_text(json.dumps({"client_reference": "x", "title": "T", "body": "B",
                                   "status": "bogus"}))
    code, out = run("publish_post.py", ["--content", str(content)])
    assert code == 1


def test_reconcile_all_published(tmp_path):
    ledger = tmp_path / "l.json"
    ledger.write_text(json.dumps([
        {"provider": "wp", "status": "published"},
        {"provider": "meta", "status": "published"}]))
    code, out = run("reconcile_publish.py", ["--ledger", str(ledger)])
    assert code == 0 and out["unknown"] == 0


def test_reconcile_unknown_blocks_close(tmp_path):
    ledger = tmp_path / "l.json"
    ledger.write_text(json.dumps([
        {"provider": "wp", "status": "published"},
        {"provider": "meta", "status": "unknown"}]))
    code, out = run("reconcile_publish.py", ["--ledger", str(ledger)])
    assert code == 1 and out["unknown"] == 1


def test_reconcile_partial(tmp_path):
    ledger = tmp_path / "l.json"
    ledger.write_text(json.dumps([
        {"provider": "wp", "status": "published"},
        {"provider": "meta", "status": "partial"}]))
    code, out = run("reconcile_publish.py", ["--ledger", str(ledger)])
    assert code == 0 and out["partial"] == 1
