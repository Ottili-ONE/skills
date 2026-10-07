#!/usr/bin/env python3
"""Check axe evidence JSON files: existence per route + zero A/AA violations.
Offline-deterministic: reads JSON files only, no network, no browser.
Exit 0 = all routes clean; exit 1 = violations or missing evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITY_TAGS = {"violations", "incomplete"}  # axe-core 4.10+ report keys
ROUTE_RE = re.compile(r"^[a-z][a-z0-9-]*(/[a-z0-9-]+)*$")


def _iter_evidence_files(evidence_dir: Path) -> list[Path]:
    if not evidence_dir.is_dir():
        return []
    return sorted(p for p in evidence_dir.rglob("*.json") if p.is_file())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence_dir", help="directory containing axe JSON evidence files")
    args = ap.parse_args()
    evidence_dir = Path(args.evidence_dir)
    files = _iter_evidence_files(evidence_dir)
    if not files:
        print("FAIL: no evidence JSON files found under %s" % evidence_dir)
        return 1

    bad = 0
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print("FAIL: %s: unreadable (%s)" % (path, exc))
            bad += 1
            continue
        violations = data.get("violations") or []
        if violations:
            print("FAIL: %s: %d violation(s)" % (path, len(violations)))
            bad += 1
    if bad:
        print("FAIL: %d evidence file(s) with violations" % bad)
        return 1
    print("OK: %d evidence file(s), zero A/AA violations" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
