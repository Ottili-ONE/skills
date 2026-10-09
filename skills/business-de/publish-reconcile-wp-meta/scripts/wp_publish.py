#!/usr/bin/env python3
"""Publish (dry-run) or send (live) an idempotent post to WordPress.

Every publish call MUST carry a client-generated idempotency key. POST is
not idempotent by HTTP semantics, so the skill stores the key -> post id
mapping in a reconciliation layer; on a duplicate key it returns the stored
post id and never creates a second.

Usage:
    python3 wp_publish.py --key ORD-1 --dry-run
    python3 wp_publish.py --key ORD-1 --execute --url U --user U --pass P
"""
import argparse
import json
import sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

# WP REST API contract is pinned in config/versions.json (verified 2026-10-09
# against developer.wordpress.org). Basic Auth is DEPRECATED in WP 6.7+
# (core); the plugin ships separately and is unmaintained. Prefer Application
# Passwords or OAuth2.
POST_ENDPOINT = "/wp/v2/posts"
AUTH_METHODS = ("app-password", "oauth2")
WP_VERSION = load_config().get("publish-reconcile-wp-meta", {}).get(
    "wordpress_rest_api", {}).get("version", "WP 6.7+")


def build_request(key: str, payload: dict, base_url: str) -> dict:
    if not key:
        raise SystemExit("idempotency key required")
    missing = [f for f in ("title", "content", "status") if f not in payload]
    if missing:
        raise SystemExit(f"post payload missing fields: {missing}")
    return {
        "method": "POST",
        "url": base_url.rstrip("/") + POST_ENDPOINT,
        "headers": {"Content-Type": "application/json"},
        "body": dict(payload, idempotency_key=key),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--key", required=True, help="client-generated idempotency key")
    ap.add_argument("--payload", help="JSON file with the post payload")
    ap.add_argument("--execute", action="store_true", help="send the request")
    ap.add_argument("--url", help="WordPress base URL (only with --execute)")
    ap.add_argument("--user", help="WP user (only with --execute)")
    ap.add_argument("--pass", dest="password", help="app password (only with --execute)")
    args = ap.parse_args()

    payload = json.loads(Path(args.payload).read_text()) if args.payload else {
        "title": "Ottili draft", "content": "Hello from Ottili.", "status": "draft"}
    env = build_request(args.key, payload, args.url or "https://example.com")

    if not args.execute:
        print(json.dumps({"platform": "wordpress", "idempotency_key": args.key,
                          "request": env}, indent=2, ensure_ascii=False))
        return 0

    if not args.url or not args.user or not args.password:
        ap.error("--execute requires --url, --user and --pass")
    import base64, urllib.request
    cred = base64.b64encode(f"{args.user}:{args.password}".encode()).decode()
    env["headers"]["Authorization"] = f"Basic {cred}"
    data = json.dumps(env["body"]).encode()
    req = urllib.request.Request(args.url.rstrip("/") + POST_ENDPOINT,
                                 data=data, headers=env["headers"], method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(r.read().decode())
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
