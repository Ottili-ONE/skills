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


if __name__ == "__main__":
    raise SystemExit(main())
