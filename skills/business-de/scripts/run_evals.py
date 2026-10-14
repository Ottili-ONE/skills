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

# Match `python3 ...` commands, in either form used by the EVALS files:
#   * inline code spans: `python3 ...` (one line)
#   * fenced ```bash blocks (multi-line, the "Run these checks" sections)
# Multi-line commands are joined into one shell command before execution.
INLINE_RE = re.compile(r"`(python3\s+\S.*?)`", re.M)
FENCE_RE = re.compile(r"```(?:bash|sh)?\n(.*?)\n```", re.S)


def extract_commands(text: str) -> list[tuple[str, int]]:
    """Return every `python3 ...` command in an EVALS.md with its expected exit.

    Two forms are accepted:
      * inline code spans: `python3 ...`
      * fenced ```bash blocks, which may hold several commands and may use
        a backslash line-continuation. The expected exit for a command is
        taken from the nearest preceding `# exits N` annotation line;
        annotations default to 0 when absent.
    """
    cmds: list[tuple[str, int]] = []
    for m in INLINE_RE.finditer(text):
        cmds.append((m.group(1), 0))
    for block in FENCE_RE.findall(text):
        raw = block.replace("\\n", " ")
        pending = 0
        for raw_line in raw.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                mm = re.search(r"\bexits?\s+(\d+)\b", line)
                if mm:
                    pending = int(mm.group(1))
                continue
            if not line.startswith("python3 "):
                continue
            # an annotation may sit on the command line itself
            # (`... --journal x.json  # exits 2`); honour it, then strip it.
            inline = re.search(r"\bexits?\s+(\d+)\b", line)
            want = pending or (int(inline.group(1)) if inline else 0)
            pending = 0
            line = re.sub(r"\s*#.*$", "", line).strip()
            if line:
                cmds.append((line, want))
    return cmds


EXIT_RE = re.compile(r"\b(?:exits?|exit code)\s+(\d+)", re.I)


def split_blocks(text: str) -> list[str]:
    """Split an EVALS.md into prompt blocks at ## / ### headers.

    A near-miss prompt that says ``exits 2`` means the command must exit 2;
    treating every non-zero exit as a failure made every near-miss fail.
    """
    blocks: list[str] = []
    cur: list[str] = []
    for line in text.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            if cur:
                blocks.append("\n".join(cur))
            cur = [line]
        else:
            cur.append(line)
    if cur:
        blocks.append("\n".join(cur))
    return blocks


def expected_exit(block: str) -> int:
    m = EXIT_RE.search(block)
    return int(m.group(1)) if m else 0


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
        blocks = split_blocks(text)
        cmds = extract_commands(text)
        if not cmds:
            print(f"[{s}] no inline python3 commands in EVALS.md — SKIPPED")
            continue
        for cmd, want_inline in cmds:
            ran += 1
            # A near-miss prompt may legitimately expect a non-zero exit
            # (``exits 2``). Read the expected code from the prompt block.
            block = next((b for b in blocks if cmd in b), text)
            want = want_inline or expected_exit(block)
            # process substitution <(...) is a shell feature; wrap it.
            full = cmd if "<(" not in cmd else f"bash -c '{cmd}'"
            r = subprocess.run(
                ["bash", "-c", full],
                cwd=str(SKILLS_DIR / s),
                capture_output=True, text=True, timeout=60,
            )
            ok = r.returncode == want
            if not ok:
                failures += 1
            status = "OK  " if ok else "FAIL"
            print(f"{status} [{s}] {cmd[:80]}{'...' if len(cmd) > 80 else ''}"
                  f" (expected exit {want})")
            if not ok:
                print(f"      exit={r.returncode} stderr={r.stderr.strip()[:300]}")
    print(f"\n{ran} commands run, {failures} failed (exit codes matched per prompt)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
