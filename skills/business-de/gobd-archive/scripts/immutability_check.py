#!/usr/bin/env python3
"""Verify a GoBD archive has no in-place modifications (hash-chain check).

Usage:
    python3 immutability_check.py --archive ./archive --state ./state.json
    python3 immutability_check.py --archive ./archive --state ./state.json --strict
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
    args = ap.parse_args()

    archive = Path(args.archive)
    state_path = Path(args.state)
    try:
        current = scan(archive)
    except NotADirectoryError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 2

    prev = {}
    if state_path.exists():
        try:
            prev = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(json.dumps({"ok": False, "error": f"corrupt state file: {e}"}))
            return 2

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

    state_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "checked": len(current),
        "violations": violations,
        "new_files": new_files,
        "state": str(state_path),
    }, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
