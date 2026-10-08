#!/usr/bin/env python3
"""Verify a GoBD archive has no in-place modifications (hash-chain check).

Usage:
    python3 immutability_check.py --archive ./archive --state ./state.json
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import sha256_of  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--state", default="immutability-state.json")
    args = ap.parse_args()

    archive = Path(args.archive)
    state_path = Path(args.state)
    prev = {}
    if state_path.exists():
        prev = json.loads(state_path.read_text(encoding="utf-8"))

    current = {}
    ok = True
    for f in sorted(p for p in archive.iterdir() if p.is_file()):
        digest = sha256_of(f)
        current[f.name] = digest
        if f.name in prev and prev[f.name] != digest:
            ok = False
            print(f"MODIFIED in place: {f.name}")
        elif f.name not in prev:
            print(f"new (append-only ok): {f.name}")

    state_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "checked": len(current),
                      "state": str(state_path)}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
