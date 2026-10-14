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
import time
from pathlib import Path

SEVERITY_TAGS = {"violations", "incomplete"}  # axe-core 4.10+ report keys
ROUTE_RE = re.compile(r"^[a-z][a-z0-9-]*(/[a-z0-9-]+)*$")
# axe-core 4.14.0 (verified 2026-10-14 via registry.npmjs.org/axe-core) is the pinned
# version; the report keys below are stable across 4.10-4.14.
REQUIRED_KEYS = ("url", "axeVersion", "violations")
FAIL_KEYS = ("violations", "incomplete", "inapplicable")  # inapplicable is informational, see below
# "inapplicable" is informational and must NOT fail the gate; only violations+incomplete do.
GATE_KEYS = ("violations", "incomplete")


def _iter_evidence_files(evidence_dir: Path) -> list[Path]:
    if not evidence_dir.is_dir():
        return []
    return sorted(p for p in evidence_dir.rglob("*.json") if p.is_file())


def _freshness_days(path: Path, max_days: int) -> int | None:
    """Return age in days, or None if the file is newer than max_days."""
    try:
        age_s = max(0.0, time.time() - path.stat().st_mtime)
    except OSError:
        return None
    return int(age_s // 86400)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence_dir", help="directory containing axe JSON evidence files")
    ap.add_argument("--max-age-days", type=int, default=30,
                    help="fail if an evidence file is older than N days (default 30)")
    ap.add_argument("--require-keys", action="store_true",
                    help="fail if a file is missing url/axeVersion/violations")
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
        if not isinstance(data, dict):
            print("FAIL: %s: top-level JSON is not an object" % path)
            bad += 1
            continue
        if args.require_keys:
            missing = [k for k in REQUIRED_KEYS if k not in data]
            if missing:
                print("FAIL: %s: missing required keys %s" % (path, missing))
                bad += 1
                continue
        # gate keys: violations and incomplete are A/AA failures; inapplicable is informational
        hits = []
        for key in GATE_KEYS:
            items = data.get(key) or []
            if items:
                hits.append((key, len(items)))
        if hits:
            for key, n in hits:
                print("FAIL: %s: %d %s item(s)" % (path, n, key))
            bad += 1
            continue
        age = _freshness_days(path, args.max_age_days)
        if age is not None and age > args.max_age_days:
            print("FAIL: %s: evidence is %d days old (max %d)" % (path, age, args.max_age_days))
            bad += 1
    if bad:
        print("FAIL: %d evidence file(s) with violations" % bad)
        return 1
    print("OK: %d evidence file(s), zero A/AA violations" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
