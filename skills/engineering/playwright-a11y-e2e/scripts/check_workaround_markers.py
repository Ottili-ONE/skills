#!/usr/bin/env python3
"""Check that every workaround in a source tree carries an ISSUE-<digits> marker.

A workaround without a linked ticket is a stale escape hatch, not a tracked workaround.
Offline-deterministic: no network, no subprocesses.
Exit 0 = all markers linked; 1 = findings; 2 = usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORKAROUND_RE = re.compile(r"(?:WORKAROUND|FV2-WA|data-ottili-workaround)", re.IGNORECASE)
ISSUE_RE = re.compile(r"ISSUE-(\d+)")


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings: list[str] = []
    for i, line in enumerate(text.splitlines()):
        if WORKAROUND_RE.search(line) and not ISSUE_RE.search(line):
            findings.append(f"{path}:{i + 1}: workaround without ISSUE-<digits> ticket")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", help="files or directories to scan")
    args = ap.parse_args()

    findings: list[str] = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            for f in sorted(path.rglob("*")):
                if f.is_file() and f.suffix in {".ts", ".tsx", ".js", ".jsx", ".css", ".py"}:
                    findings.extend(check_file(f))
        elif path.is_file():
            findings.extend(check_file(path))

    if findings:
        print(f"FAIL: {len(findings)} unlinked workaround(s)")
        for f in findings:
            print(f"  - {f}")
        return 1
    print(f"ok: all workarounds in {len(args.paths)} path(s) link an ISSUE-<digits> ticket")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
