#!/usr/bin/env python3
"""Generate and self-check the GoBD Verfahrensdokumentation checklist.

The Verfahrensdokumentation is the document the auditor asks for. It must exist
for the full retention period; a missing one is a fine risk (up to EUR 50,000
under §378 AO). This script emits the six mandatory sections and, with
--check, verifies that a supplied JSON state covers all of them.

Usage:
    python3 verfahrensdokumentation.py --system "ERP v5.2" --medium "S3 encrypted" \
        --export "DATEV EXTF" --year 2026 --out vd.json
    python3 verfahrensdokumentation.py --check vd.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

# The six mandatory sections, in the order the auditor expects them.
SECTIONS = [
    ("system", "System — name, version and location of the accounting data store"),
    ("medium", "Storage medium — disk/cloud, encryption, backup medium"),
    ("retention", "Retention periods — the 6/8/10-year classes with effective date"),
    ("export", "Export format — DATEV EXTF or CSV+XML, with a manifest"),
    ("access", "Access controls — who may read/write/delete and how it is enforced"),
    ("backup", "Backup procedure — frequency, retention, restore test"),
]


def build(args: argparse.Namespace) -> dict:
    pinned = load_config(args.config)["gobd-archive"]
    return {
        "verfahrensdokumentation": {
            "generated": args.today,
            "effective_date": pinned["ao147"]["effective"],
            "sections": {
                "system": {"description": args.system, "complete": bool(args.system)},
                "medium": {"description": args.medium, "complete": bool(args.medium)},
                "retention": {"description": args.retention,
                              "complete": bool(args.retention)},
                "export": {"description": args.export, "complete": bool(args.export)},
                "access": {"description": args.access, "complete": bool(args.access)},
                "backup": {"description": args.backup, "complete": bool(args.backup)},
            },
        }
    }


def check(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    sections = doc.get("verfahrensdokumentation", {}).get("sections", {})
    missing = [name for name, _ in SECTIONS
               if not sections.get(name, {}).get("complete")]
    return {"ok": not missing, "missing_sections": missing,
            "checked": len(sections)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--system", default="")
    ap.add_argument("--medium", default="")
    ap.add_argument("--retention", default="8y vouchers / 10y books / 6y correspondence (AO §147, effective 2025-01-01)")
    ap.add_argument("--export", default="DATEV EXTF Buchungsstapel + MANIFEST.json")
    ap.add_argument("--access", default="role-based; read/write/delete separated; delete requires approval")
    ap.add_argument("--backup", default="daily incremental, weekly full, restore test quarterly")
    ap.add_argument("--config", default="config/versions.json")
    ap.add_argument("--today", default="2026-10-08")
    ap.add_argument("--out", help="write the checklist to this JSON file")
    ap.add_argument("--check", help="verify an existing checklist JSON")
    args = ap.parse_args()

    if args.check:
        try:
            result = check(Path(args.check))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(json.dumps({"ok": False, "error": str(e)}, indent=2,
                             ensure_ascii=False), file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["ok"] else 1

    doc = build(args)
    if args.out:
        Path(args.out).write_text(json.dumps(doc, indent=2, ensure_ascii=False),
                                  encoding="utf-8")
    print(json.dumps(doc, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
