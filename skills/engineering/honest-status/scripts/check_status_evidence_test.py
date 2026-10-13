#!/usr/bin/env python3
"""Offline self-tests for check_status_evidence.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "check_status_evidence.py"

GOOD = """\
## DONE
- [x] axe scan zero violations - evidence: tests/e2e/evidence/login.json

## VERIFIED
- [x] keyboard path reaches close button - evidence: tests/e2e/keyboard-login.mp4

## IN_PROGRESS
- [ ] responsive overflow on mobile - blocker: modal uses position:fixed; owner: alice

## BLOCKED
- [ ] dark mode contrast - question: does AA apply to dark mode? owner: bob

## FALSE_DONE
- [ ] ~~axe zero violations~~ - no evidence file committed; downgraded from DONE
"""

BAD = """\
## DONE
- [x] axe scan passes
- [x] keyboard path works
- [x] responsive checks pass
"""


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
        (t / "tests/e2e/evidence/login.json").parent.mkdir(parents=True, exist_ok=True)
        (t / "tests/e2e/evidence/login.json").write_text("{}", encoding="utf-8")
        (t / "tests/e2e/keyboard-login.mp4").parent.mkdir(parents=True, exist_ok=True)
        (t / "tests/e2e/keyboard-login.mp4").write_text("video", encoding="utf-8")

        good = t / "STATUS_good.md"
        good.write_text(GOOD, encoding="utf-8")
        r = run(str(good), "--root", str(t))
        if r.returncode != 0:
            print("FAIL: good STATUS should pass")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: good STATUS passes")

        bad = t / "STATUS_bad.md"
        bad.write_text(BAD, encoding="utf-8")
        r = run(str(bad), "--root", str(t))
        if r.returncode != 1:
            print("FAIL: bad STATUS should fail")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: bad STATUS fails as expected")

    if failures:
        print(f"\n{failures} test(s) failed")
        return 1
    print("\nall tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
