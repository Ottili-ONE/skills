#!/usr/bin/env python3
"""Negotiate an MCP protocol version between a client and a server.

Given two lists of supported versions, returns the agreed version (highest common)
or FAIL with the -32022 UnsupportedProtocolVersion semantics. Fully offline.

Machine-readable counts go to stdout; FAIL:/PASS:/INFO: detail goes to stderr.
"""

from __future__ import annotations

import argparse
import json
import sys

ALLOWED = ["2026-07-28", "2025-11-25", "2025-06-18"]


def negotiate(client: list[str], server: list[str]) -> str | None:
    common = [v for v in ALLOWED if v in client and v in server]
    return common[0] if common else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--client", required=True, help="comma-separated client versions")
    ap.add_argument("--server", required=True, help="comma-separated server versions")
    args = ap.parse_args()

    client = [v.strip() for v in args.client.split(",") if v.strip()]
    server = [v.strip() for v in args.server.split(",") if v.strip()]

    agreed = negotiate(client, server)
    if agreed:
        print("1 0 0")
        print(f"PASS: agreed {agreed}", file=sys.stderr)
        return 0
    print("0 1 0")
    print("FAIL: no common version; server returns -32022 UnsupportedProtocolVersion", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
