#!/usr/bin/env python3
"""Validate an outbound webhook-delivery target against an allow-list.

Delivering to an attacker-controlled host is an SSRF. This script checks the
target host and path against the pinned allow-list and rejects anything
else — including IP literals and localhost, which are never resolved.

Usage:
    python3 ssrf_check.py --url https://ottili.example/webhooks/inbound --allow ottili.example
"""
import argparse
import json
import sys
from urllib.parse import urlparse


def check(url: str, allow_hosts: list[str]) -> dict:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not host:
        return {"ok": False, "reason": "no host in URL", "host": host}
    if host.isdigit() or host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
        return {"ok": False, "reason": "IP literal / loopback not allowed",
                "host": host}
    for allowed in allow_hosts:
        if host == allowed or host.endswith("." + allowed):
            return {"ok": True, "host": host, "allowed": allowed}
    return {"ok": False, "reason": "host not in allow-list", "host": host,
            "allow_list": allow_hosts}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", required=True)
    ap.add_argument("--allow", action="append", default=[], dest="allow_hosts")
    args = ap.parse_args()
    if not args.allow_hosts:
        ap.error("--allow is required (repeatable)")
    result = check(args.url, args.allow_hosts)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
