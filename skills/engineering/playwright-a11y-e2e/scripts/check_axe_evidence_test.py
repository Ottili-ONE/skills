#!/usr/bin/env python3
"""Offline self-tests for check_axe_evidence.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "check_axe_evidence.py"


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
        clean = t / "login.json"
        clean.write_text(json.dumps({"violations": []}), encoding="utf-8")
        r = run(str(t))
        if r.returncode != 0:
            print("FAIL: clean evidence should pass")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: clean evidence passes")

        dirty = t / "broken.json"
        dirty.write_text(
            json.dumps({"violations": [{"id": "color-contrast", "impact": "AA"}]}),
            encoding="utf-8",
        )
        r = run(str(t))
        if r.returncode != 1:
            print("FAIL: evidence with violations should fail")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: evidence with violations fails as expected")

        empty = t / "empty"
        empty.mkdir()
        r = run(str(empty))
        if r.returncode != 1:
            print("FAIL: empty evidence dir should fail")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: empty evidence dir fails as expected")

        # incomplete items are also A/AA failures
        inc = t / "inc.json"
        inc.write_text(json.dumps({
            "url": "/login", "axeVersion": "4.14.0",
            "incomplete": [{"id": "region", "impact": "AA"}],
            "violations": [], "inapplicable": [],
        }), encoding="utf-8")
        r = run(str(t))
        if r.returncode != 1:
            print("FAIL: evidence with incomplete items should fail")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: incomplete items fail as expected")

        # inapplicable is informational and must NOT fail the gate
        inapp = t / "inapp.json"
        inapp.write_text(json.dumps({
            "url": "/login", "axeVersion": "4.14.0",
            "violations": [], "incomplete": [],
            "inapplicable": [{"id": "aria-implicit"}],
        }), encoding="utf-8")
        r = run(str(t))
        if r.returncode != 1:
            print("FAIL: inapplicable-only evidence should pass")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: inapplicable-only evidence passes")

        # --require-keys catches files missing url/axeVersion/violations
        r = run(str(t), "--require-keys")
        if r.returncode != 1:
            print("FAIL: --require-keys should fail on keys-missing file")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: --require-keys fails on missing keys")

        # a fully-formed file passes --require-keys
        full = t / "full.json"
        full.write_text(json.dumps({
            "url": "/login", "axeVersion": "4.14.0",
            "violations": [], "incomplete": [], "inapplicable": [],
        }), encoding="utf-8")
        r = run(str(t), "--require-keys")
        if r.returncode != 1:
            print("FAIL: fully-formed evidence should pass --require-keys")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: fully-formed evidence passes --require-keys")

    if failures:
        print(f"\n{failures} test(s) failed")
        return 1
    print("\nall tests passed")
    return 0




EDGE = [
    ("non-object JSON", "top-level JSON is not an object"),
    ("stale evidence", "evidence is"),
    ("require-keys missing", "missing required keys"),
    ("max-age-days enforced", "evidence is"),
]


def _run_edge() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # non-object JSON (own dir so earlier bad files cannot pollute it)
        d = root / "nonobject"
        d.mkdir()
        (d / "bad.json").write_text("[1, 2, 3]", encoding="utf-8")
        r = run(str(d))
        if r.returncode != 1 or "not an object" not in (r.stdout + r.stderr):
            print("FAIL: non-object JSON should fail")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: non-object JSON fails")

        # stale evidence older than --max-age-days (own dir)
        d = root / "stale"
        d.mkdir()
        old = d / "old.json"
        old.write_text(json.dumps({"violations": [], "incomplete": [],
                                    "inapplicable": []}), encoding="utf-8")
        import os as _os
        _os.utime(old, (1, 1))  # epoch -> very old
        r = run(str(d), "--max-age-days", "1")
        if r.returncode != 1 or "days old" not in (r.stdout + r.stderr):
            print("FAIL: stale evidence should fail --max-age-days")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: stale evidence fails --max-age-days")

        # --require-keys fails when url/axeVersion/violations missing (own dir)
        d = root / "nokeys"
        d.mkdir()
        (d / "nokeys.json").write_text(json.dumps({"violations": []}), encoding="utf-8")
        r = run(str(d), "--require-keys")
        if r.returncode != 1 or "missing required keys" not in (r.stdout + r.stderr):
            print("FAIL: --require-keys should fail on missing keys")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: --require-keys fails on missing keys")

        # fresh evidence within --max-age-days passes (own dir)
        d = root / "fresh"
        d.mkdir()
        (d / "fresh.json").write_text(json.dumps({
            "url": "/x", "axeVersion": "4.14.0",
            "violations": [], "incomplete": [], "inapplicable": [],
        }), encoding="utf-8")
        r = run(str(d), "--require-keys", "--max-age-days", "30")
        if r.returncode != 0:
            print("FAIL: fresh evidence with --require-keys should pass")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: fresh evidence passes --require-keys")
    return failures


if __name__ == "__main__":
    rc = main()
    if rc != 0:
        raise SystemExit(rc)
    rc = _run_edge()
    raise SystemExit(rc)
