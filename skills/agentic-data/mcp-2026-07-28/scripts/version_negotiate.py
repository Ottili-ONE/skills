#!/usr/bin/env python3
"""Negotiate an MCP protocol version between a client and a server.

Given two lists of supported versions, returns the agreed version (highest common)
or FAIL with the -32022 UnsupportedProtocolVersion semantics. Fully offline.

Machine-readable counts go to stdout; FAIL:/PASS:/INFO: detail goes to stderr.
Exit 0 on agreement, 1 on refusal, 2 on usage/input error.

Edge cases handled:
  * unknown revisions are dropped, never drive agreement (they are not in ALLOWED)
  * duplicate or empty entries in either list
  * --json emits a machine-readable {"agreed": ...|"refused": ...} object
"""

from __future__ import annotations

import argparse
import json
import sys

ALLOWED = ["2026-07-28", "2025-11-25", "2025-06-18"]


def negotiate(client: list[str], server: list[str]) -> str | None:
    """Return the highest revision present in both lists, or None.

    Only revisions in the vendored ALLOWED list may drive agreement; unknown
    entries are reported as INFO and ignored, because a server advertising a
    revision this skill does not know about is ahead of the skill, not compatible.
    """
    c = [v for v in dict.fromkeys(client) if v in ALLOWED]
    s = [v for v in dict.fromkeys(server) if v in ALLOWED]
    common = [v for v in ALLOWED if v in c and v in s]
    return common[0] if common else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--client", required=True, help="comma-separated client versions")
    ap.add_argument("--server", required=True, help="comma-separated server versions")
    ap.add_argument("--json", action="store_true",
                    help="emit a machine-readable result object to stdout")
    args = ap.parse_args()

    client_raw = [v.strip() for v in args.client.split(",") if v.strip()]
    server_raw = [v.strip() for v in args.server.split(",") if v.strip()]

    unknown_client = [v for v in client_raw if v not in ALLOWED]
    unknown_server = [v for v in server_raw if v not in ALLOWED]
    for v in unknown_client:
        print(f"INFO: client advertises unknown revision {v!r}; ignored", file=sys.stderr)
    for v in unknown_server:
        print(f"INFO: server advertises unknown revision {v!r}; ignored", file=sys.stderr)

    agreed = negotiate(client_raw, server_raw)
    if args.json:
        # Machine-readable mode: JSON object to stdout ONLY, no counts line.
        if agreed:
            print(json.dumps({"agreed": agreed, "refused": None}))
            print(f"PASS: agreed {agreed}", file=sys.stderr)
            return 0
        print(json.dumps({"agreed": None, "refused": "-32022"}))
        print("FAIL: no common version; server returns -32022 UnsupportedProtocolVersion",
              file=sys.stderr)
        return 1
    if agreed:
        print("1 0 0")
        print(f"PASS: agreed {agreed}", file=sys.stderr)
        return 0
    print("0 1 0")
    print("FAIL: no common version; server returns -32022 UnsupportedProtocolVersion", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
