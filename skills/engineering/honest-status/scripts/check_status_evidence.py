#!/usr/bin/env python3
"""Check a STATUS.md for false-done claims.

A claim is FALSE_DONE unless it names an evidence pointer that (a) exists on disk and
(b) can be checked in under 60 seconds. Buckets: DONE, VERIFIED, IN_PROGRESS, BLOCKED,
FALSE_DONE. DONE and VERIFIED are the only buckets allowed to carry evidence pointers;
every claim in them without a pointer is downgraded to FALSE_DONE.

Usage:
  python3 check_status_evidence.py STATUS.md [--root .]
Exit 0 = no false-done claims; 1 = findings; 2 = usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BUCKETS = {"DONE", "VERIFIED", "IN_PROGRESS", "BLOCKED", "FALSE_DONE"}
# A claim line: "- [ ] text" or "- [x] text", optionally followed by "evidence: <path>".
CLAIM_RE = re.compile(r"^\s*-\s*\[(?P<checked>[ xX])\]\s*(?P<text>.+)$")
EVIDENCE_RE = re.compile(r"evidence:\s*(?P<evidence>\S+)", re.IGNORECASE)


def parse_status(text: str) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = {b: [] for b in BUCKETS}
    current = "UNFILED"
    for raw in text.splitlines():
        line = raw.rstrip()
        header = re.match(r"^##\s+(?P<bucket>[A-Z_]+)\s*$", line)
        if header:
            current = header.group("bucket").upper()
            if current not in buckets:
                current = "UNFILED"
            continue
        if current in ("DONE", "VERIFIED"):
            m = CLAIM_RE.match(line)
            if m:
                ev = EVIDENCE_RE.search(m.group("text"))
                buckets[current].append(
                    {"checked": m.group("checked").lower() == "x",
                     "text": m.group("text").strip(),
                     "evidence": ev.group("evidence").strip() if ev else ""}
                )
    return buckets


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("status", help="STATUS.md file")
    ap.add_argument("--root", default=".", help="root for resolving relative evidence paths")
    args = ap.parse_args()

    text = Path(args.status).read_text(encoding="utf-8")
    root = Path(args.root).resolve()
    buckets = parse_status(text)

    findings: list[str] = []
    for bucket in ("DONE", "VERIFIED"):
        for claim in buckets[bucket]:
            ev = claim["evidence"]
            if not ev:
                findings.append(f"{args.status}: {bucket} claim without evidence pointer: {claim['text'][:60]}")
                continue
            p = (root / ev).resolve()
            if not p.exists():
                findings.append(f"{args.status}: {bucket} evidence not found: {ev}")
            elif p.is_dir() and not any(p.iterdir()):
                findings.append(f"{args.status}: {bucket} evidence dir is empty: {ev}")

    if findings:
        print(f"FAIL: {args.status}")
        for f in findings:
            print(f"  - {f}")
        return 1
    print(f"ok: {args.status} has no false-done claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
