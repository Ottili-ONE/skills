#!/usr/bin/env python3
"""Offline self-tests for check_audit_selectors.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "check_audit_selectors.py"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        clean = t / "clean.json"
        clean.write_text(json.dumps({"suites": [{"tests": [{"title": "ok", "steps": []}]}]}), encoding="utf-8")
        r = run(str(clean))
        if r.returncode != 0:
            print("FAIL: clean report should pass")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: clean report passes")

        dirty = t / "dirty.json"
        dirty.write_text(
            json.dumps({"suites": [{"tests": [{"title": "bad", "steps": [{"selector": "div:nth-child(3)"}]}]}]}),
            encoding="utf-8",
        )
        r = run(str(dirty))
        if r.returncode != 1:
            print("FAIL: report with nth-child should fail")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: report with nth-child fails as expected")

    if failures:
        print(f"\n{failures} test(s) failed")
        return 1
    print("\nall tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
