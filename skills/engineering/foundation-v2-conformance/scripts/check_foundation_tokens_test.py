#!/usr/bin/env python3
"""Offline self-tests for check_foundation_tokens.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "check_foundation_tokens.py"

TOKENS = {
    "color": {"brand": "#1a73e8", "text": "#202124"},
    "spacing": {"md": "16px", "lg": "24px"},
}


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
        tok = t / "tokens.json"
        tok.write_text(json.dumps(TOKENS), encoding="utf-8")

        clean = t / "clean.css"
        clean.write_text(".btn { color: #1a73e8; padding: 16px; }", encoding="utf-8")
        r = run("--tokens", str(tok), str(clean))
        if r.returncode != 0:
            print("FAIL: clean file should pass")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: clean file passes")

        dirty = t / "dirty.css"
        dirty.write_text(".btn { color: #deadbeef; padding: 99px; }", encoding="utf-8")
        r = run("--tokens", str(tok), str(dirty))
        if r.returncode != 1:
            print("FAIL: dirty file should fail")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: dirty file fails as expected")

        allowed = t / "allowed.css"
        allowed.write_text(
            ".btn { color: #deadbeef; padding: 99px; } /* ALLOWED: FV2-WA ISSUE-1234 */",
            encoding="utf-8",
        )
        r = run("--tokens", str(tok), "--allow-comment", "ALLOWED", str(allowed))
        if r.returncode != 0:
            print("FAIL: allowed-comment file should pass")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: allowed-comment file passes")

    if failures:
        print(f"\n{failures} test(s) failed")
        return 1
    print("\nall tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
