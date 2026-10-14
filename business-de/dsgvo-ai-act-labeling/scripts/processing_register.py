#!/usr/bin/env python3
"""Emit an Art. 30 GDPR processing-register row and validate its required fields.

The register is the living document a supervisory authority asks for. This
script takes a use-case description + retention class and emits one row,
exiting non-zero when a required field is missing so a half-row cannot be
committed.

Usage:
    python3 processing_register.py --use-case usecase.json --out register.jsonl
"""
import argparse
import json
import sys
from pathlib import Path

REQUIRED = [
    "use_case_id", "purpose", "data_categories", "data_subjects",
    "lawful_basis", "retention_class", "processor_list",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--use-case", required=True, help="use-case JSON file")
    ap.add_argument("--out", required=True, help="register jsonl output")
    args = ap.parse_args()

    uc = json.loads(Path(args.use_case).read_text(encoding="utf-8"))
    missing = [f for f in REQUIRED if f not in uc or uc[f] in (None, '')]
    if missing:
        print(json.dumps({"ok": False, "missing": missing}))
        return 1
    row = {f: uc[f] for f in REQUIRED}
    row["retention_years"] = uc.get("retention_years")
    with Path(args.out).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"ok": True, "row": row, "out": args.out}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
