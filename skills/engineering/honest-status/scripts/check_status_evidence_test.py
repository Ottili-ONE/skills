#!/usr/bin/env python3
"""Offline self-tests for check_status_evidence.py."""
from __future__ import annotations

import json

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

# A VERIFIED claim with no evidence pointer is FALSE_DONE: VERIFIED means the
# check ran and passed but the change is not yet integrated, so it still needs a
# runnable pointer to the check output.
UNVERIFIED_VERIFIED = """\
## VERIFIED
- [x] leak test green locally - status: VERIFIED (not merged)
"""

# IN_PROGRESS without a blocker and BLOCKED without an owner/question are stranded
# claims: nobody knows what is stuck or who to ask.
STRANDED = """\
## IN_PROGRESS
- [ ] tenant_id backfill

## BLOCKED
- [ ] dark mode contrast
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




EDGE = """\
## DONE
- [x] axe scan zero violations
  evidence: tests/e2e/evidence/login.json

## VERIFIED
- [x] keyboard path reaches close button
  evidence: tests/e2e/keyboard-login.mp4

## FALSE_DONE
- [ ] ~~axe zero violations~~ - no evidence file committed; downgraded from DONE
"""


def test_next_line_evidence() -> None:
    """An `evidence:` line on its own following the claim carries the pointer."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "tests/e2e/evidence/login.json").parent.mkdir(parents=True, exist_ok=True)
        (t / "tests/e2e/evidence/login.json").write_text("{}", encoding="utf-8")
        (t / "tests/e2e/keyboard-login.mp4").parent.mkdir(parents=True, exist_ok=True)
        (t / "tests/e2e/keyboard-login.mp4").write_text("video", encoding="utf-8")
        f = t / "STATUS.md"
        f.write_text(EDGE, encoding="utf-8")
        r = run(str(f), "--root", str(t))
        if r.returncode != 0:
            print("FAIL: next-line evidence should pass")
            print(r.stdout, r.stderr)
            return 1
        print("ok: next-line evidence is accepted")
        return 0


def test_empty_evidence_file() -> None:
    """An evidence pointer to an empty file is not evidence; downgraded."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "empty.log").write_text("", encoding="utf-8")
        f = t / "STATUS.md"
        f.write_text("## DONE\n- [x] build passed - evidence: empty.log\n", encoding="utf-8")
        r = run(str(f), "--root", str(t))
        if r.returncode != 1 or "empty" not in (r.stdout + r.stderr):
            print("FAIL: empty evidence file should be downgraded")
            print(r.stdout, r.stderr)
            return 1
        print("ok: empty evidence file is downgraded")
        return 0


def test_false_done_checked_contradiction() -> None:
    """A [x] claim under FALSE_DONE is still claiming done; must be flagged."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        f = t / "STATUS.md"
        f.write_text(
            "## FALSE_DONE\n- [x] ~~migration applied~~ - no evidence\n",
            encoding="utf-8",
        )
        r = run(str(f), "--root", str(t))
        if r.returncode != 1 or "contradiction" not in (r.stdout + r.stderr):
            print("FAIL: checked claim under FALSE_DONE should be flagged")
            print(r.stdout, r.stderr)
            return 1
        print("ok: FALSE_DONE contradiction is flagged")
        return 0


def test_json_output() -> None:
    """--json emits machine-readable status with bucket counts."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "x.json").write_text("{}", encoding="utf-8")
        f = t / "STATUS.md"
        f.write_text("## DONE\n- [x] x - evidence: x.json\n", encoding="utf-8")
        r = run(str(f), "--root", str(t), "--json")
        if r.returncode != 0:
            print("FAIL: --json on a clean STATUS should exit 0")
            print(r.stdout, r.stderr)
            return 1
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            print("FAIL: --json output is not valid JSON:", r.stdout)
            return 1
        if data.get("status") != "ok" or data.get("buckets", {}).get("DONE") != 1:
            print("FAIL: --json status/buckets wrong:", data)
            return 1
        print("ok: --json output is valid and correct")
        return 0


def test_json_output_findings() -> None:
    """--json on a finding emits status=fail with the finding list."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        f = t / "STATUS.md"
        f.write_text("## DONE\n- [x] done\n", encoding="utf-8")
        r = run(str(f), "--root", str(t), "--json")
        if r.returncode != 1:
            print("FAIL: --json with findings should exit 1")
            print(r.stdout, r.stderr)
            return 1
        data = json.loads(r.stdout)
        if data.get("status") != "fail" or not data.get("findings"):
            print("FAIL: --json findings wrong:", data)
            return 1
        print("ok: --json findings output is correct")
        return 0


def test_usage_error() -> None:
    """Missing argument exits 2."""
    r = run()
    if r.returncode != 2:
        print("FAIL: missing arg should exit 2, got", r.returncode)
        return 1
    print("ok: usage error exits 2")
    return 0


def test_unreadable_status() -> None:
    """A STATUS.md that cannot be read exits 2, not a crash."""
    r = run("/nonexistent/STATUS.md")
    if r.returncode != 2:
        print("FAIL: unreadable STATUS should exit 2, got", r.returncode)
        return 1
    print("ok: unreadable STATUS exits 2")
    return 0


def test_unverified_verified_is_false_done() -> None:
    """A VERIFIED claim that is not a checked item with evidence is FALSE_DONE."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "leak.log").write_text("ok", encoding="utf-8")
        f = t / "STATUS.md"
        f.write_text(UNVERIFIED_VERIFIED, encoding="utf-8")
        r = run(str(f), "--root", str(t))
        if r.returncode != 1 or "VERIFIED" not in (r.stdout + r.stderr):
            print("FAIL: unchecked VERIFIED should be flagged")
            print(r.stdout, r.stderr)
            return 1
        print("ok: unchecked VERIFIED is downgraded")
        return 0


def test_stranded_in_progress_and_blocked() -> None:
    """IN_PROGRESS needs a blocker; BLOCKED needs an owner and a question."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        f = t / "STATUS.md"
        f.write_text(STRANDED, encoding="utf-8")
        r = run(str(f), "--root", str(t))
        if r.returncode != 1:
            print("FAIL: stranded IN_PROGRESS/BLOCKED should fail")
            print(r.stdout, r.stderr)
            return 1
        out = r.stdout + r.stderr
        if "no blocker named" not in out or "no owner named" not in out:
            print("FAIL: stranded claims should name the missing fields")
            print(out)
            return 1
        print("ok: stranded IN_PROGRESS/BLOCKED are flagged")
        return 0


EDGE_TESTS = [
    ("unverified verified is false done", test_unverified_verified_is_false_done),
    ("stranded in-progress and blocked", test_stranded_in_progress_and_blocked),
    ("next-line evidence", test_next_line_evidence),
    ("empty evidence file", test_empty_evidence_file),
    ("FALSE_DONE contradiction", test_false_done_checked_contradiction),
    ("json output", test_json_output),
    ("json output findings", test_json_output_findings),
    ("usage error", test_usage_error),
    ("unreadable status", test_unreadable_status),
]


def run_edge() -> int:
    failures = 0
    for name, fn in EDGE_TESTS:
        try:
            failures += fn()
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: {name} raised {exc!r}")
            failures += 1
    return failures


if __name__ == "__main__":
    rc = main()
    if rc != 0:
        raise SystemExit(rc)
    rc = run_edge()
    raise SystemExit(rc)
