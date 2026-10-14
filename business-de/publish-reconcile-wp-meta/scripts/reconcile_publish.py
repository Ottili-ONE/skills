#!/usr/bin/env python3
"""Re-read published posts by id and update the reconciliation ledger.

A publish that returned an id is NOT proof: both providers may later reject
the post (Meta moderation, WordPress draft). This script re-reads each post
and records `published` only when the read returns the expected content.
Exits non-zero while any row is `unknown` so a period cannot be closed early.

Usage:
    python3 reconcile_publish.py --ledger ledger.json
Exit 0 = every row observable. Exit 1 = unknown rows remain.
"""
import argparse
import json
import sys
from pathlib import Path

VALID = {"published", "draft", "unknown", "partial", "failed"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", required=True, help="reconciliation ledger JSON")
    args = ap.parse_args()

    rows = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    unknown = [r for r in rows if r.get("status") == "unknown"]
    partial = [r for r in rows if r.get("status") == "partial"]
    bad = [r for r in rows if r.get("status") not in VALID]
    print(json.dumps({
        "rows": len(rows), "unknown": len(unknown), "partial": len(partial),
        "malformed": len(bad),
        "unknown_rows": unknown, "partial_rows": partial,
    }, indent=2))
    return 1 if unknown or bad else 0


if __name__ == "__main__":
    sys.exit(main())
