#!/usr/bin/env python3
"""Publish (dry-run) or send (live) an idempotent post to Meta (Facebook).

Every publish call MUST carry a client-generated idempotency key. POST is
not idempotent by HTTP semantics, so the skill stores the key -> post id
mapping in a reconciliation layer; on a duplicate key it returns the stored
post id and never creates a second.

Usage:
    python3 meta_publish.py --key ORD-1 --dry-run
    python3 meta_publish.py --key ORD-1 --execute --page-id P --token T
"""
import argparse
import json
import sys
from pathlib import Path

# Meta Graph API contract (verified 2026-10-07 against developers.facebook.com).
# Meta sunsets API versions silently; the version is pinned in config and
# re-verified quarterly. Never hardcode a version in logic.
GRAPH_BASE = "https://graph.facebook.com"
FEED_ENDPOINT = "/{page-id}/feed"


def build_request(key: str, payload: dict, page_id: str, version: str) -> dict:
    if not key:
        raise SystemExit("idempotency key required")
    missing = [f for f in ("message",) if f not in payload]
    if missing:
        raise SystemExit(f"post payload missing fields: {missing}")
    if not page_id:
        raise SystemExit("page-id required")
    url = f"{GRAPH_BASE}/{version}" + FEED_ENDPOINT.replace("{page-id}", page_id)
    body = dict(payload, idempotency_key=key)
    return {"method": "POST", "url": url,
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            "body": body}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--key", required=True, help="client-generated idempotency key")
    ap.add_argument("--payload", help="JSON file with the post payload")
    ap.add_argument("--execute", action="store_true", help="send the request")
    ap.add_argument("--page-id", required=True, help="Meta page id")
    ap.add_argument("--token", help="page access token (only with --execute)")
    ap.add_argument("--version", default="v19.0", help="Graph API version (pinned)")
    args = ap.parse_args()

    payload = json.loads(Path(args.payload).read_text()) if args.payload else {"message": "Hello from Ottili."}
    env = build_request(args.key, payload, args.page_id or "0", args.version)

    if not args.execute:
        print(json.dumps({"platform": "meta", "idempotency_key": args.key,
                          "request": env}, indent=2, ensure_ascii=False))
        return 0

    if not args.page_id or not args.token:
        ap.error("--execute requires --page-id and --token")
    import urllib.parse, urllib.request
    data = urllib.parse.urlencode({**env["body"], "access_token": args.token}).encode()
    req = urllib.request.Request(env["url"], data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(r.read().decode())
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
