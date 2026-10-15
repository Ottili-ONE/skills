#!/usr/bin/env python3
"""Verify a GoBD archive has no in-place modifications (hash-chain check).

Usage:
    python3 immutability_check.py --archive ./archive --state ./state.json
    python3 immutability_check.py --archive ./archive --state ./state.json --strict
    python3 immutability_check.py --archive ./archive --state ./state.json --write-state

The script is **read-only by default**: it never rewrites the state file
unless ``--write-state`` is passed. A GoBD audit check must not modify the
archive's own bookkeeping; pass ``--write-state`` only when you are seeding a
first state or knowingly refreshing it.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import sha256_of  # noqa: E402


def scan(archive: Path) -> dict:
    """Return {name: sha256} for every file, sorted by name."""
    if not archive.is_dir():
        raise NotADirectoryError(f"archive is not a directory: {archive}")
    out = {}
    for f in sorted(p for p in archive.iterdir() if p.is_file()):
        out[f.name] = sha256_of(f)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--state", default="immutability-state.json")
    ap.add_argument("--strict", action="store_true",
                    help="fail if any file is new (append-only is expected, "
                         "not required for a first run)")
    ap.add_argument("--write-state", action="store_true",
                    help="actually rewrite the state file (opt-in; "
                         "the default is read-only)")
    ap.add_argument("--init-state", action="store_true",
                    help="seed a brand-new state file when none exists yet "
                         "(first run only; implies --write-state)")
    args = ap.parse_args()

    archive = Path(args.archive)
    state_path = Path(args.state)
    try:
        current = scan(archive)
    except NotADirectoryError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 2

    prev = {}
    first_run = not state_path.exists()
    if state_path.exists():
        try:
            prev = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(json.dumps({"ok": False, "error": f"corrupt state file: {e}"}))
            return 2
    elif not args.init_state:
        # Read-only by default: a missing state file is a *result*, not an
        # error -- it means no baseline has been recorded yet. Tell the
        # caller how to create one instead of silently writing one.
        print(json.dumps({
            "ok": True,
            "checked": len(current),
            "state": "missing",
            "state_path": str(state_path),
            "next": "re-run with --init-state to record the baseline",
            "violations": [],
            "new_files": sorted(current),
        }, indent=2))
        return 0

    ok = True
    violations = []
    new_files = []
    for name, digest in current.items():
        if name in prev:
            if prev[name] != digest:
                ok = False
                violations.append(name)
        else:
            new_files.append(name)
    for name in prev:
        if name not in current:
            ok = False
            violations.append(f"{name} (deleted)")

    if args.strict and new_files:
        ok = False
        violations.append(f"new files under --strict: {new_files}")

    if args.write_state or (args.init_state and first_run):
        state_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "checked": len(current),
        "violations": violations,
        "new_files": new_files,
        "state": str(state_path),
        "state_written": bool(args.write_state or (args.init_state and first_run)),
    }, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
