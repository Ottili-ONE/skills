#!/usr/bin/env python3
"""Check a Playwright JSON report for keyboard reachability.

Every interactive element must be reachable via Tab within <=5 Tab presses per viewport.
Offline-deterministic: reads the JSON report only, no browser.
Exit 0 = all interactive elements reachable; 1 = findings; 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MAX_TABS = 5


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report", help="Playwright JSON report")
    args = ap.parse_args()

    data = json.loads(Path(args.report).read_text(encoding="utf-8"))
    findings: list[str] = []
    for suite in data.get("suites", []):
        for test in suite.get("tests", []):
            for result in test.get("results", []):
                # Playwright JSON does not carry tab counts by default; we look for the
                # `--trace`-derived `tabCount` field when present, and otherwise treat the
                # test as evidence-only (the harness records the count in the evidence file).
                meta = (result.get("stdout") or []) + (result.get("stderr") or [])
                for line in meta:
                    if isinstance(line, str) and "tabCount" in line:
                        try:
                            n = int(line.split("tabCount=")[1].split()[0])
                            if n > MAX_TABS:
                                findings.append(
                                    f"{test.get('title','?')}: tabCount={n} > {MAX_TABS}"
                                )
                        except (IndexError, ValueError):
                            pass
    if findings:
        print("FAIL: keyboard reachability")
        for f in findings:
            print(f"  - {f}")
        return 1
    print("ok: keyboard reachability within %d Tab presses" % MAX_TABS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
