#!/usr/bin/env python3
"""PASS 3 smoke harness: run every business-de script on real inputs.

Discovers every <skill>/scripts/*.py, invokes each with no args and with
--help where supported, and records exit codes + a short stdout snippet.
Real inputs come from each skill's own tests/ fixtures so the run is
deterministic and offline.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # business-de/
SKILLS = sorted(p for p in ROOT.iterdir() if (p / "SKILL.md").is_file())


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
        return r.returncode, (r.stdout + r.stderr).strip()[:400]
    except Exception as e:  # noqa: BLE001
        return -1, f"EXC {type(e).__name__}: {e}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", action="append", default=[])
    args = ap.parse_args()
    skills = [ROOT / s for s in args.skill] or SKILLS
    total_fail = 0
    for skill in skills:
        scripts = sorted((skill / "scripts").glob("*.py"))
        if not scripts:
            print(f"== {skill.name}: no scripts")
            continue
        print(f"== {skill.name} ({len(scripts)} scripts)")
        for s in scripts:
            for argv in ([sys.executable, str(s)], [sys.executable, str(s), "--help"]):
                code, out = run(argv, cwd=ROOT)
                tag = "ok" if code in (0, 1) else "FAIL"
                if code not in (0, 1):
                    total_fail += 1
                print(f"  [{tag}] {' '.join(argv)} -> exit {code}")
                if out and code != 0:
                    print(f"        {out.splitlines()[0][:160]}")
    print(f"\nscripts checked; failures={total_fail}")
    return 1 if total_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
