#!/usr/bin/env python3
"""Check shared-tree git safety rules for the current working tree.

Offline-deterministic: no network calls, no subprocesses beyond stdlib os/git-lite checks.
Small (<200 LOC), runs <1s on typical Ottili repos.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


FORBIDDEN = ["reset --hard", "checkout ", "stash", "rebase", "merge ", "pull", "add -A", "add .", "commit -a"]
COMMIT_PREFIX_RE = re.compile(r"^[a-z0-9-]+-r3-[0-9]+:")


def _git(args: list[str], cwd: str | None = None) -> str:
    """Run a read-only git command; return stdout or empty on failure."""
    try:
        out = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=15
        )
        return out.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def _index_lock(cwd: str) -> tuple[bool, str]:
    """Return (exists, holder_pid) for .git/index.lock."""
    path = Path(cwd) / ".git" / "index.lock"
    if not path.is_file():
        return False, ""
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    m = re.search(r"\d+", text)
    pid = m.group(0) if m else ""
    return True, pid


def _pid_alive(pid: str) -> bool:
    if not pid.isdigit():
        return False
    try:
        os.kill(int(pid), 0)
    except OSError:
        return False
    return True


def cmd_locks(args: argparse.Namespace) -> int:
    exists, pid = _index_lock(args.cwd)
    if not exists:
        print("ok: no index.lock present")
        return 0
    if pid and _pid_alive(pid):
        print(f"error: index.lock held by live PID {pid}; wait or ask holder", file=sys.stderr)
        return 1
    print(f"warn: stale index.lock (PID {pid or 'unknown'} dead); safe to remove")
    return 0


def cmd_staged(args: argparse.Namespace) -> int:
    """Verify staged paths are all owned by this task."""
    staged = _git(["diff", "--cached", "--name-only"], args.cwd).splitlines()
    staged = [s for s in staged if s.strip()]
    if not staged:
        print("ok: nothing staged")
        return 0
    bad = [s for s in staged if not s.startswith(args.owned_prefix)]
    if bad:
        print("error: staged paths outside owned prefix:", file=sys.stderr)
        for b in bad:
            print(f"  - {b}", file=sys.stderr)
        return 1
    print(f"ok: {len(staged)} staged paths all under {args.owned_prefix}")
    return 0


def cmd_message(args: argparse.Namespace) -> int:
    """Check a commit message for the task-id prefix."""
    if not COMMIT_PREFIX_RE.match(args.message):
        print(f"error: commit message missing task-id prefix; got: {args.message!r}", file=sys.stderr)
        return 1
    print(f"ok: commit message starts with task-id prefix")
    return 0


def cmd_scan_forbidden(args: argparse.Namespace) -> int:
    """Scan a shell script for forbidden shared-tree commands."""
    text = Path(args.file).read_text(encoding="utf-8", errors="ignore")
    hits = []
    for needle in FORBIDDEN:
        if needle in text:
            hits.append(needle)
    if hits:
        print("error: forbidden shared-tree commands found:", file=sys.stderr)
        for h in hits:
            print(f"  - {h}", file=sys.stderr)
        return 1
    print("ok: no forbidden shared-tree commands")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Shared-tree git safety checker")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--owned-prefix", default="skills/engineering/")
    parser.add_argument("--message", default=None)
    parser.add_argument("--file", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("locks")
    sub.add_parser("staged")
    sub.add_parser("message")
    sub.add_parser("scan")
    args = parser.parse_args()
    if args.cmd == "locks":
        return cmd_locks(args)
    if args.cmd == "staged":
        return cmd_staged(args)
    if args.cmd == "message":
        return cmd_message(args)
    if args.cmd == "scan":
        return cmd_scan_forbidden(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
