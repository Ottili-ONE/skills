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


def test_require_ticket_rejects_marker_without_ticket() -> None:
    """--require-ticket turns a bare ALLOWED marker back into a finding."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "token.json").write_text(json.dumps({"colors": ["#1a1a1a"], "spacing": ["1rem"]}))
        src = t / "comp.tsx"
        src.write_text(
            "import { Button } from '@ottili/foundation-ui';\n"
            "const c = <div style={{ color: '#ff0000' }} ALLOWED />\n",
            encoding="utf-8",
        )
        r = run("--tokens", str(t / "token.json"), "--require-ticket", str(src))
        if r.returncode != 1 or "#ff0000" not in (r.stdout + r.stderr):
            print("FAIL: marker without ticket should be a finding under --require-ticket")
            print(r.stdout, r.stderr)
            return 1
        print("ok: --require-ticket rejects a bare ALLOWED marker")
        return 0


def test_require_ticket_accepts_marker_with_ticket() -> None:
    """A marker carrying FV2-WA: ISSUE-<digits> and owner: is exempt."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "token.json").write_text(json.dumps({"colors": ["#1a1a1a"], "spacing": ["1rem"]}))
        src = t / "comp.tsx"
        src.write_text(
            "import { Button } from '@ottili/foundation-ui';\n"
            "<div style={{ color: '#ff0000' }} /* ALLOWED: FV2-WA: ISSUE-1234 owner: alice */ />\n",
            encoding="utf-8",
        )
        r = run("--tokens", str(t / "token.json"), "--require-ticket", str(src))
        if r.returncode != 0:
            print("FAIL: ticketed marker should be exempt")
            print(r.stdout, r.stderr)
            return 1
        print("ok: --require-ticket accepts a ticketed marker")
        return 0


EDGE_TESTS = [
    ("require-ticket rejects bare marker", test_require_ticket_rejects_marker_without_ticket),
    ("require-ticket accepts ticketed marker", test_require_ticket_accepts_marker_with_ticket),
]


def run_edge() -> int:
    failures = 0
    for _name, fn in EDGE_TESTS:
        try:
            failures += fn()
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: {_name} raised {exc!r}")
            failures += 1
    return failures


if __name__ == "__main__":
    rc = main()
    if rc != 0:
        raise SystemExit(rc)
    rc = run_edge()
    raise SystemExit(rc)
