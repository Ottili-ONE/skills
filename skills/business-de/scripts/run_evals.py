#!/usr/bin/env python3
"""Run every EVALS.md prompt's script example against the real script.

Reads references/EVALS.md for each skill, extracts the `python3 ...` command
lines, executes them with a sandboxed CWD, and reports pass/fail. This is the
"execute the evals" half of the quality pass — a prompt whose script example
does not run is a broken prompt.

Usage:
    python3 skills/business-de/scripts/run_evals.py [skill-name ...]
Exit 0 if every extracted command exits 0, 1 otherwise.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = ROOT / "skills" / "business-de"

CMD_RE = re.compile(r"`(python3\s+\S+[^`]*?)`", re.M)


def evals_files(skills):
    out = []
    for s in skills:
        ev = SKILLS_DIR / s / "references" / "EVALS.md"
        if ev.is_file():
            out.append((s, ev))
    return out


def main(argv):
    skills = argv or sorted(
        p.name for p in SKILLS_DIR.iterdir()
        if (p / "references" / "EVALS.md").is_file()
    )
    failures = 0
    ran = 0
    for s, ev in evals_files(skills):
        text = ev.read_text(encoding="utf-8")
        cmds = CMD_RE.findall(text)
        if not cmds:
            print(f"[{s}] no inline python3 commands in EVALS.md — SKIPPED")
            continue
        for cmd in cmds:
            ran += 1
            # process substitution <(...) is a shell feature; wrap it.
            full = cmd if "<(" not in cmd else f"bash -c '{cmd}'"
            r = subprocess.run(
                ["bash", "-c", full],
                cwd=str(SKILLS_DIR / s),
                capture_output=True, text=True, timeout=60,
            )
            ok = r.returncode == 0
            if not ok:
                failures += 1
            status = "OK  " if ok else "FAIL"
            print(f"{status} [{s}] {cmd[:96]}{'...' if len(cmd) > 96 else ''}")
            if not ok:
                print(f"      exit={r.returncode} stderr={r.stderr.strip()[:300]}")
    print(f"\n{ran} commands run, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
