#!/usr/bin/env python3
"""Offline self-tests for report_result.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "report_result.py"


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
        out = t / "results.json"
        r = run(
            "--scenario", "S-1", "--outcome", "PASS", "--evidence", "login.json",
            "--criterion", "HTTP 200", "--output", str(out),
        )
        if r.returncode != 0:
            print("FAIL: PASS write should succeed")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: PASS write succeeds")
            data = json.loads(out.read_text())
            assert data["results"][0]["outcome"] == "PASS"

        r = run(
            "--scenario", "S-2", "--outcome", "MAYBE", "--evidence", "x.json",
            "--output", str(out),
        )
        if r.returncode != 2:
            print("FAIL: invalid outcome should exit 2")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: invalid outcome exits 2")

        r = run(
            "--scenario", "S-1", "--outcome", "FAIL", "--evidence", "login.json",
            "--criterion", "HTTP 500", "--output", str(out),
        )
        if r.returncode != 0:
            print("FAIL: overwrite of existing scenario should succeed")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: scenario overwritten")
            data = json.loads(out.read_text())
            assert len(data["results"]) == 1
            assert data["results"][0]["outcome"] == "FAIL"

    if failures:
        print(f"\n{failures} test(s) failed")
        return 1
    print("\nall tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
