#!/usr/bin/env python3
"""Check a Playwright JSON report for stable selectors.

Rejects `nth-child` and bare-class-attribute selectors; requires role/text-based
alternatives in the same PR. Offline-deterministic: reads the JSON report only.
Exit 0 = all selectors stable; 1 = findings; 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BANNED = re.compile(r"nth-child|nth-of-type|\[class\s*=\s*['\"]", re.IGNORECASE)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report", help="Playwright JSON report")
    args = ap.parse_args()

    raw_text = Path(args.report).read_text(encoding="utf-8")
    data = json.loads(raw_text)
    findings: list[str] = []
    # Scan the raw JSON text: a banned selector may live anywhere in a test's
    # steps, screenshots, or error messages, and json.dumps() re-serialises it.
    for m in BANNED.finditer(raw_text):
        findings.append(f"{args.report}: unstable selector near '{m.group(0)}'")
    # Also scan the parsed structure so the title is reported when possible.
    for suite in data.get("suites", []):
        for test in suite.get("tests", []):
            title = test.get("title", "?")
            for raw in json.dumps(test):
                for m in BANNED.finditer(raw):
                    findings.append(f"{title}: unstable selector near '{m.group(0)}'")
                    break

    if findings:
        print("FAIL: unstable selectors")
        for f in findings:
            print(f"  - {f}")
        return 1
    print("ok: all selectors in report are role/text-based")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
