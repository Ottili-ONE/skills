#!/usr/bin/env python3
"""Produce a GoBD-compliant audit export: chronological, checksummed, with a manifest.

Usage:
    python3 audit_export.py --source ./archive --output ./export --year 2026
    python3 audit_export.py --source ./archive --output ./export --year 2026 --verify
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import sha256_of  # noqa: E402

MANIFEST = "MANIFEST.json"


def export(source: Path, output: Path, year: int, today: str) -> dict:
    """Copy every file chronologically and write a checksummed manifest."""
    if not source.is_dir():
        raise NotADirectoryError(f"source is not a directory: {source}")
    output.mkdir(parents=True, exist_ok=True)

    files = sorted(p for p in source.iterdir() if p.is_file() and p.name != MANIFEST)
    manifest = []
    for f in files:
        dest = output / f.name
        shutil.copy2(f, dest)
        manifest.append({
            "file": f.name,
            "sha256": sha256_of(dest),
            "exported": today,
            "period": year,
        })
    manifest_path = output / MANIFEST
    manifest_path.write_text(json.dumps({
        "export": today,
        "period": year,
        "file_count": len(manifest),
        "files": manifest,
        "format": "original-files-plus-manifest",
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"export_dir": str(output), "manifest": str(manifest_path),
            "files": len(manifest)}


def verify_export(output: Path, today: str) -> dict:
    """Re-check every exported file against the manifest."""
    manifest_path = output / MANIFEST
    if not manifest_path.exists():
        raise FileNotFoundError(f"no manifest at {manifest_path}")
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatches = []
    for entry in doc.get("files", []):
        p = output / entry["file"]
        if not p.exists():
            mismatches.append(f"{entry['file']} missing from export")
        elif sha256_of(p) != entry["sha256"]:
            mismatches.append(f"{entry['file']} checksum mismatch")
    return {"ok": not mismatches, "mismatches": mismatches,
            "verified": today, "files": len(doc.get("files", []))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, help="archive directory")
    ap.add_argument("--output", required=True, help="export directory")
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--verify", action="store_true",
                    help="re-check exported files against the manifest")
    ap.add_argument("--today", default="2026-10-08",
                    help="export timestamp (default 2026-10-08)")
    args = ap.parse_args()

    try:
        result = export(Path(args.source), Path(args.output), args.year, args.today)
        if args.verify:
            result["verify"] = verify_export(Path(args.output), args.today)
    except (NotADirectoryError, FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2,
                         ensure_ascii=False), file=sys.stderr)
        return 2

    print(json.dumps({"ok": True, **result}, indent=2, ensure_ascii=False))
    return 0 if result.get("verify", {}).get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
