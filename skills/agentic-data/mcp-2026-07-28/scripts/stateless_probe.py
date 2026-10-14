#!/usr/bin/env python3
"""Probe an MCP deployment for statelessness.

Given two JSON-RPC request/response pairs with identical _meta, asserts the results
are identical and that no session state is implied. Fully offline.

Machine-readable counts go to stdout; FAIL:/PASS:/INFO: detail goes to stderr.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("a", help="first request/response pair JSON")
    ap.add_argument("b", help="second request/response pair JSON")
    args = ap.parse_args()

    try:
        a, b = load(args.a), load(args.b)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: could not read input: {exc}", file=sys.stderr)
        return 1

    fails = 0
    for name, pair in (("a", a), ("b", b)):
        if not isinstance(pair, dict):
            print(f"FAIL: {name} is not a JSON object, got {type(pair).__name__}",
                  file=sys.stderr)
            fails += 1
    if fails:
        print(f"0 {fails} 0")
        return 1

    ma = a.get("_meta", {})
    mb = b.get("_meta", {})
    if not ma:
        print("FAIL: a._meta is empty; per-request metadata is mandatory",
              file=sys.stderr)
        fails += 1
    if ma != mb:
        print("FAIL: _meta differs between replays; request is not self-contained", file=sys.stderr)
        fails += 1
    if ma.get("io.modelcontextprotocol/protocolVersion") in (None, ""):
        print("FAIL: _meta missing protocolVersion", file=sys.stderr)
        fails += 1

    ra, rb = a.get("result"), b.get("result")
    if ra != rb:
        print("FAIL: results differ across identical replays", file=sys.stderr)
        fails += 1

    def _scan(obj, where):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if "session" in str(k).lower():
                    print(f"FAIL: {where} carries a session key {k!r}; 2026-07-28 is stateless", file=sys.stderr)
                    return True
                if _scan(v, where):
                    return True
        return False

    for name, pair in (("a", a), ("b", b)):
        if _scan(pair, name):
            fails += 1

    if fails:
        print(f"0 {fails} 0")
        return 1
    print("1 0 0")
    print("PASS: replay identical, _meta complete, no session state", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
