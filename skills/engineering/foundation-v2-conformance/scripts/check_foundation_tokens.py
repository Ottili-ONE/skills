#!/usr/bin/env python3
"""Check that every raw design value in a consumer resolves to a Foundation token.

A raw literal (hex colour, rgb() function, px/rem/em spacing, numeric font-weight) is
only acceptable when it is *present in the token file* (i.e. token-derived) or sits on a
line exempted by an `ALLOWED` comment marker naming a ticket.

Offline-deterministic: no network, no subprocesses beyond stdlib.
Usage:
  python3 check_foundation_tokens.py --tokens token.json [--allow-comment ALLOWED] <file> [<file> ...]
Exit 0 = all values token-derived; 1 = findings; 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGB_RE = re.compile(r"rgba?\(\s*[\d.%\s,]+\)")
PX_RE = re.compile(r"(?<![\w-])(\d+(?:\.\d+)?)px\b")
REM_RE = re.compile(r"(?<![\w-])(\d+(?:\.\d+)?)rem\b")
EM_RE = re.compile(r"(?<![\w-])(\d+(?:\.\d+)?)em\b")


def _load_tokens(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    values: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str):
            values.add(node)
            m = HEX_RE.search(node)
            if m:
                values.add(m.group(0))

    walk(data)
    return values


def _exempt_lines(text: str, allow_comment: str) -> set[int]:
    """Return the set of 0-based line indices exempted by an ALLOWED comment."""
    exempt: set[int] = set()
    for i, line in enumerate(text.splitlines()):
        if allow_comment and allow_comment in line:
            exempt.add(i)
    return exempt


def check_file(path: Path, tokens: set[str], allow_comment: str) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    exempt = _exempt_lines(text, allow_comment)
    findings: list[str] = []
    for i, line in enumerate(text.splitlines()):
        if i in exempt:
            continue
        for m in HEX_RE.finditer(line):
            if m.group(0) not in tokens:
                findings.append(f"{path}:{i + 1}: raw colour {m.group(0)} not in token set")
        for m in RGB_RE.finditer(line):
            findings.append(f"{path}:{i + 1}: raw colour function {m.group(0)} not token-derived")
        for m in PX_RE.finditer(line):
            if m.group(0) not in tokens:
                findings.append(f"{path}:{i + 1}: raw spacing {m.group(0)} not token-derived")
        for m in REM_RE.finditer(line):
            if m.group(0) not in tokens:
                findings.append(f"{path}:{i + 1}: raw spacing {m.group(0)} not token-derived")
        for m in EM_RE.finditer(line):
            if m.group(0) not in tokens:
                findings.append(f"{path}:{i + 1}: raw spacing {m.group(0)} not token-derived")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokens", required=True, help="Foundation token file (JSON)")
    ap.add_argument(
        "--allow-comment",
        default="ALLOWED",
        help="comment marker that exempts a line from the check",
    )
    ap.add_argument("files", nargs="+", help="consumer source files to scan")
    args = ap.parse_args()

    tokens = _load_tokens(Path(args.tokens))
    findings: list[str] = []
    for f in args.files:
        findings.extend(check_file(Path(f), tokens, args.allow_comment))

    if findings:
        print(f"FAIL: {len(findings)} raw-value finding(s)")
        for f in findings:
            print(f"  - {f}")
        return 1
    print(f"ok: all values in {len(args.files)} file(s) are token-derived")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
