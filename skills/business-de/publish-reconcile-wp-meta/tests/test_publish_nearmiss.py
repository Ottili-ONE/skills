"""Near-miss trigger tests for publish-reconcile-wp-meta.

The traps: a duplicate idempotency key must return the existing post id, never
mint a second one; an unknown result must be re-queried by key, never acted on;
and a persistent mismatch must be flagged for human review, never silently
overwritten.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "scripts" / "reconcile.py"
STORE = ROOT / "scripts" / "idempotency_store.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True)


def test_duplicate_key_returns_existing_post(tmp_path):
    """Recording a mapping then looking it up must return the SAME post id,
    never a new one."""
    store = tmp_path / "store.jsonl"
    r1 = run(STORE, "--key", "ORD-1", "--platform", "wordpress",
             "--post-id", "42", "--store", str(store))
    assert r1.returncode == 0, r1.stderr
    r2 = run(STORE, "--key", "ORD-1", "--platform", "wordpress",
             "--lookup", "--store", str(store))
    assert r2.returncode == 0
    out = json.loads(r2.stdout)
    assert out["found"] is True
    assert out["post_id"] == "42"


def test_lookup_missing_key_is_not_a_create(tmp_path):
    """A missing key is not a signal to publish — it is a signal to publish
    FOR THE FIRST TIME. Looking up a missing key must not record anything."""
    store = tmp_path / "store.jsonl"
    r = run(STORE, "--key", "ORD-2", "--platform", "wordpress",
            "--lookup", "--store", str(store))
    assert r.returncode == 1  # not found, not a silent create
    out = json.loads(r.stdout)
    assert out["found"] is False
    assert not store.exists() or store.read_text().strip() == ""


def test_reconcile_unknown_result_flagged(tmp_path):
    """When one platform times out the result is unknown; re-query both by key
    and log the delta rather than acting on either answer."""
    wp = tmp_path / "wp.json"
    wp.write_text(json.dumps({"idempotency_key": "ORD-3", "id": None, "status": "unknown"}))
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps({"idempotency_key": "ORD-3", "id": None, "status": "unknown"}))
    r = run(RECON, "--key", "ORD-3", "--wp", str(wp), "--meta", str(meta))
    assert r.returncode == 1
    out = json.loads(r.stdout)
    assert out["ok"] is False
    assert "unknown" in json.dumps(out).lower()


def test_reconcile_persistent_mismatch_flagged_for_review(tmp_path):
    """A persistent mismatch is flagged, never silently overwritten."""
    wp = tmp_path / "wp.json"
    wp.write_text(json.dumps({"idempotency_key": "ORD-4", "id": "100", "status": "published"}))
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps({"idempotency_key": "ORD-4", "id": "200", "status": "published"}))
    r = run(RECON, "--key", "ORD-4", "--wp", str(wp), "--meta", str(meta))
    assert r.returncode == 1
    out = json.loads(r.stdout)
    assert out["ok"] is False
    assert any("differs" in d.get("reason", "") or "human" in json.dumps(out).lower()
               for d in out["deltas"])


def test_reconcile_both_agree_is_ok(tmp_path):
    wp = tmp_path / "wp.json"
    wp.write_text(json.dumps({"idempotency_key": "ORD-5", "id": "300", "status": "published"}))
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps({"idempotency_key": "ORD-5", "id": "300", "status": "published"}))
    r = run(RECON, "--key", "ORD-5", "--wp", str(wp), "--meta", str(meta))
    assert r.returncode == 0, r.stdout
    out = json.loads(r.stdout)
    assert out["ok"] is True
    assert out["deltas"] == []


def test_store_is_append_only(tmp_path):
    """Recording two mappings appends two lines; the store is never mutated
    in place, so the history is auditable."""
    store = tmp_path / "store.jsonl"
    run(STORE, "--key", "A", "--platform", "wordpress", "--post-id", "1", "--store", str(store))
    run(STORE, "--key", "B", "--platform", "wordpress", "--post-id", "2", "--store", str(store))
    lines = [l for l in store.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
