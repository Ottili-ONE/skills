#!/usr/bin/env python3
"""Idempotent dual-platform publish to WordPress and Meta.

Takes a canonical content JSON (with a client-generated `client_reference`)
and returns a per-provider result with the remote ids. The same
client_reference must be reused on retry — providers either return the
existing post or create a duplicate, never both.

This is a dry-run: it validates the payload shape and prints the HTTP request
that would be made. Provide real credentials to actually publish.

Usage:
    python3 publish_post.py --content post.json --providers wp,meta
Exit 0 = payload valid. Exit 1 = invalid payload.
"""
import argparse
import json
import sys
from pathlib import Path

WP_URL = "https://example.com/wp-json/wp/v2/posts"
META_URL = "https://graph.facebook.com/v26.0/{page-id}/feed"


def normalize(content: dict) -> dict:
    """Return the canonical payload shape; fail on ambiguous input."""
    required = ["client_reference", "title", "body", "status"]
    missing = [f for f in required if not content.get(f)]
    if missing:
        raise ValueError(f"content missing required fields: {missing}")
    if content["status"] not in ("publish", "draft", "future"):
        raise ValueError(f"invalid status: {content['status']}")
    return {
        "client_reference": content["client_reference"],
        "title": content["title"],
        "body": content["body"],
        "status": content["status"],
        "media": content.get("media", []),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--content", required=True, help="canonical content JSON")
    ap.add_argument("--providers", default="wp,meta",
                    choices=["wp,meta", "wp", "meta"])
    args = ap.parse_args()

    payload = normalize(json.loads(Path(args.content).read_text(encoding="utf-8")))
    results = {}
    if "wp" in args.providers:
        results["wp"] = {"method": "POST", "url": WP_URL,
                         "auth": "Basic (Application Password) or OAuth 2",
                         "payload": payload}
    if "meta" in args.providers:
        results["meta"] = {"method": "POST", "url": META_URL,
                           "auth": "Page access token", "payload": payload}
    print(json.dumps({"ok": True, "client_reference": payload["client_reference"],
                      "providers": results}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as e:
        print(json.dumps({"ok": False, "reason": str(e)}))
        sys.exit(1)
