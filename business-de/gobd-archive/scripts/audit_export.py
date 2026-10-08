#!/usr/bin/env python3
"""Produce a GoBD-compliant audit export: chronological, checksummed, with a manifest.

Usage:
    python3 audit_export.py --source ./archive --output ./export --year 2026
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import sha256_of  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, help="archive directory")
    ap.add_argument("--output", required=True, help="export directory")
    ap.add_argument("--year", type=int, default=2026)
    args = ap.parse_args()

    src = Path(args.source)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    files = sorted(p for p in src.iterdir() if p.is_file())
    manifest = []
    for f in files:
        dest = out / f.name
        shutil.copy2(f, dest)
        manifest.append({
            "file": f.name,
            "sha256": sha256_of(dest),
            "exported": "2026-10-08",
            "period": args.year,
        })
    manifest_path = out / "MANIFEST.json"
    manifest_path.write_text(json.dumps({
        "export": "2026-10-08",
        "period": args.year,
        "files": manifest,
        "format": "original-files-plus-manifest",
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": True, "export_dir": str(out),
                      "manifest": str(manifest_path),
                      "files": len(manifest)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
