#!/usr/bin/env python3
"""Offline self-tests for check_workaround_markers.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "check_workaround_markers.py"


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
        linked = t / "linked.tsx"
        linked.write_text(
            "const x = 1; /* FV2-WA: ISSUE-1234 */\n", encoding="utf-8"
        )
        r = run(str(linked))
        if r.returncode != 0:
            print("FAIL: linked marker should pass")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: linked marker passes")

        unlinked = t / "unlinked.tsx"
        unlinked.write_text(
            "const x = 1; /* WORKAROUND: remove later */\n", encoding="utf-8"
        )
        r = run(str(unlinked))
        if r.returncode != 1:
            print("FAIL: unlinked marker should fail")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: unlinked marker fails as expected")

    if failures:
        print(f"\n{failures} test(s) failed")
        return 1
    print("\nall tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
