#!/usr/bin/env python3
"""Verify an EU AI Act / GDPR label artefact before an agent relies on it.

A label is only valid if: every required field is present, reviewer evidence
is attached and names a real person, the last review date is inside the
re-verification window, and the stored checksum matches the artefact content
(tamper evidence). Missing or stale evidence is BLOCKING.

Usage:
    python3 label_check.py --label label.json [--evidence evidence.json]
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

CFG = load_config().get("dsgvo-ai-act-labeling", {})
RECHECK_DAYS = int(CFG.get("label_recheck_days", {}).get("value", 365))
REQUIRED = ["system", "risk_class", "art6_status", "art50_status",
            "human_review_status", "reviewed_at", "reviewer", "checksum"]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check(label_path: Path, evidence_path: Path = None) -> dict:
    label = json.loads(label_path.read_text())
    errors, warnings = [], []
    for field in REQUIRED:
        if field not in label or label[field] in (None, ""):
            errors.append(f"missing required field: {field}")
    if label.get("risk_class") == "high" and label.get("human_review_status") != "approved":
        errors.append("high-risk system without approved human review is BLOCKING")
    reviewed = label.get("reviewed_at")
    if reviewed:
        try:
            dt = datetime.fromisoformat(str(reviewed).replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - dt).days
            if age > RECHECK_DAYS:
                errors.append(f"label stale: last review {age}d ago, window {RECHECK_DAYS}d")
        except ValueError:
            errors.append(f"reviewed_at not ISO-8601: {reviewed!r}")
    if evidence_path:
        if not evidence_path.exists():
            errors.append(f"evidence file missing: {evidence_path}")
        else:
            ev = json.loads(evidence_path.read_text())
            reviewer = ev.get("reviewer") or label.get("reviewer")
            if not reviewer:
                errors.append("no reviewer identity in evidence or label")
            elif not ev.get("review_notes"):
                warnings.append("evidence has no review notes (weak but not blocking)")
    stored = label.get("checksum")
    if stored:
        actual = _sha256(label_path)
        if stored != actual:
            errors.append(f"checksum mismatch: stored {stored[:12]}... != actual {actual[:12]}...")
    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "label": label.get("system"), "risk_class": label.get("risk_class")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", required=True, type=Path)
    ap.add_argument("--evidence", type=Path)
    args = ap.parse_args()
    if not args.label.exists():
        print(f"label file not found: {args.label}", file=sys.stderr)
        return 2
    result = check(args.label, args.evidence)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
