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


        # URL/SVG url() spans must not false-positive as raw colours
        urlcss = t / "url.css"
        urlcss.write_text(
            ".a { background: url(#clip-1); } .b { background: url(https://x.com/img#fff); }",
            encoding="utf-8",
        )
        r = run("--tokens", str(tok), str(urlcss))
        if r.returncode != 0:
            print("FAIL: url(#clip-1) and URL hashes should not be findings")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: url()/URL spans excluded from colour scan")

        # --json emits machine-readable output
        rj = run("--tokens", str(tok), "--json", str(dirty))
        if rj.returncode != 1:
            print("FAIL: --json should still exit 1 on findings")
            print(rj.stdout, rj.stderr)
            failures += 1
        else:
            try:
                data = json.loads(rj.stdout)
                assert data["status"] == "fail"
                assert data["total_findings"] >= 2
                print("ok: --json emits machine-readable report")
            except Exception as exc:
                print("FAIL: --json output not parseable:", exc)
                failures += 1

        # --max-findings caps per-file findings
        rmax = run("--tokens", str(tok), "--max-findings", "1", str(dirty))
        if rmax.returncode != 1:
            print("FAIL: --max-findings should fail when exceeded")
            print(rmax.stdout, rmax.stderr)
            failures += 1
        else:
            print("ok: --max-findings fails when exceeded")

    if failures:
        print(f"\n{failures} test(s) failed")
        return 1
    print("\nall tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
