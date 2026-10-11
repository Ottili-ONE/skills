#!/usr/bin/env python3
"""Validate an MCP server's server/discover response against the 2026-07-28 contract.

Reads a JSON document (file argument or stdin) describing a discover response and
checks the MUST-level fields. Fully offline and deterministic.

Machine-readable counts go to stdout; FAIL:/PASS:/WARN:/INFO: detail goes to stderr.
Exit 0 on success, 1 on any FAIL.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ALLOWED_VERSIONS = {"2026-07-28", "2025-11-25", "2025-06-18"}
REQUIRED_RESULT_KEYS = {"supportedVersions", "capabilities", "serverInfo"}
REQUIRED_SERVER_INFO_KEYS = {"name", "version"}


def load(path: str | None) -> dict:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def check(doc: dict) -> tuple[int, int, int]:
    fails = warns = oks = 0
    result = doc.get("result", doc)

    missing = REQUIRED_RESULT_KEYS - set(result)
    if missing:
        print(f"FAIL: server/discover result missing keys: {sorted(missing)}", file=sys.stderr)
        fails += 1
    else:
        oks += 1

    versions = result.get("supportedVersions")
    if not isinstance(versions, list) or not versions:
        print("FAIL: supportedVersions must be a non-empty list", file=sys.stderr)
        fails += 1
    else:
        unknown = [v for v in versions if v not in ALLOWED_VERSIONS]
        if unknown:
            print(f"WARN: supportedVersions contains unknown revisions: {unknown}", file=sys.stderr)
            warns += 1
        if "2026-07-28" not in versions:
            print("INFO: server does not advertise 2026-07-28", file=sys.stderr)
        oks += 1

    info = result.get("serverInfo")
    if not isinstance(info, dict):
        print("FAIL: serverInfo must be an object with name and version", file=sys.stderr)
        fails += 1
    else:
        lack = REQUIRED_SERVER_INFO_KEYS - set(info)
        if lack:
            print(f"FAIL: serverInfo missing keys: {sorted(lack)}", file=sys.stderr)
            fails += 1
        else:
            oks += 1

    return fails, warns, oks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", nargs="?", help="JSON file (default: stdin)")
    args = ap.parse_args()

    try:
        doc = load(args.file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: could not read input: {exc}", file=sys.stderr)
        return 1

    fails, warns, oks = check(doc)
    print(f"{oks} {fails} {warns}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
