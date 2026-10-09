"""Offline, deterministic tests for the publish-reconcile-wp-meta scripts."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WP = ROOT / "scripts" / "wp_publish.py"
META = ROOT / "scripts" / "meta_publish.py"
RECON = ROOT / "scripts" / "reconcile.py"
IDSTORE = ROOT / "scripts" / "idempotency_store.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True)


def test_wp_publish_has_idempotency_key():
    r = run(WP, "--key", "ORD-1")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["idempotency_key"] == "ORD-1"
    assert data["request"]["body"]["idempotency_key"] == "ORD-1"
    assert data["request"]["url"].endswith("/wp/v2/posts")


def test_wp_publish_requires_key():
    r = run(WP, "--key", "")
    assert r.returncode != 0


def test_meta_publish_has_idempotency_key():
    r = run(META, "--key", "ORD-2", "--page-id", "123")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["idempotency_key"] == "ORD-2"
    assert "graph.facebook.com" in data["request"]["url"]
    assert "/123/feed" in data["request"]["url"]


def test_meta_publish_requires_page_id():
    r = run(META, "--key", "ORD-3")
    assert r.returncode != 0


def test_reconcile_match():
    wp = {"idempotency_key": "ORD-1", "id": 42}
    meta = {"idempotency_key": "ORD-1", "id": "99"}
    wp_path = Path("/tmp/_pub_wp.json"); wp_path.write_text(json.dumps(wp))
    meta_path = Path("/tmp/_pub_meta.json"); meta_path.write_text(json.dumps(meta))
    r = run(RECON, "--key", "ORD-1", "--wp", str(wp_path), "--meta", str(meta_path))
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["ok"] is True


def test_reconcile_mismatch():
    wp = {"idempotency_key": "ORD-1", "id": 42}
    meta = {"idempotency_key": "ORD-9", "id": "99"}
    wp_path = Path("/tmp/_pub_wp2.json"); wp_path.write_text(json.dumps(wp))
    meta_path = Path("/tmp/_pub_meta2.json"); meta_path.write_text(json.dumps(meta))
    r = run(RECON, "--key", "ORD-1", "--wp", str(wp_path), "--meta", str(meta_path))
    assert r.returncode == 1, r.stderr
    deltas = json.loads(r.stdout)["deltas"]
    assert any(d["platform"] == "meta" for d in deltas)


def test_idempotency_store_records_and_looks_up():
    import tempfile, os
    store = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    store.close()
    r = run(IDSTORE, "--key", "ORD-1", "--platform", "wordpress",
            "--post-id", "42", "--store", store.name)
    assert r.returncode == 0, r.stderr
    r2 = run(IDSTORE, "--key", "ORD-1", "--platform", "wordpress",
             "--lookup", "--store", store.name)
    os.unlink(store.name)
    assert r2.returncode == 0, r2.stderr
    data = json.loads(r2.stdout)
    assert data["found"] is True
    assert data["post_id"] == "42"


def test_idempotency_store_lookup_miss():
    import tempfile, os
    store = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    store.close()
    r = run(IDSTORE, "--key", "MISSING", "--platform", "wordpress",
            "--lookup", "--store", store.name)
    os.unlink(store.name)
    assert r.returncode == 1, r.stderr
    assert json.loads(r.stdout)["found"] is False


def test_idempotency_store_append_only():
    import tempfile, os
    store = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    store.close()
    run(IDSTORE, "--key", "ORD-1", "--platform", "wordpress", "--post-id", "42",
        "--store", store.name)
    run(IDSTORE, "--key", "ORD-1", "--platform", "wordpress", "--post-id", "43",
        "--store", store.name)
    lines = Path(store.name).read_text().splitlines()
    os.unlink(store.name)
    assert len(lines) == 2  # never mutated in place
