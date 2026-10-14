#!/usr/bin/env python3
"""Apply the EU AI Act Art. 50(4) exception test to a review-record JSON.

Art. 50(4) requires disclosure of AI-generated text published to inform the
public — UNLESS the text has undergone qualified human review AND a natural or
legal person holds editorial responsibility. Both conjuncts must be true.

Usage:
    python3 label_check.py --record review.json
Exit 0 = EXEMPT. Exit 1 = LABEL (disclose). Exit 2 = usage error.
"""
import argparse
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

REQUIRED_FIELDS = [
    "content_id", "reviewer", "review_date", "review_decision",
    "editorial_responsibility_holder", "review_evidence_path",
]


def load_record(path: Path) -> dict:
    rec = json.loads(path.read_text(encoding="utf-8"))
    missing = [f for f in REQUIRED_FIELDS if not rec.get(f)]
    if missing:
        raise ValueError(f"review record missing required fields: {missing}")
    return rec


def evidence_intact(path: Path) -> bool:
    """The review evidence must exist and its checksum must match the record."""
    if not path.exists():
        return False
    recorded = path.parent / (path.name + ".sha256")
    if not recorded.exists():
        return False
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return recorded.read_text(encoding="utf-8").strip() == h


def review_within_window(rec: dict, days: int) -> bool:
    """A review older than the window is stale and must be re-done."""
    rd = rec.get("review_date")
    try:
        d = datetime.strptime(rd, "%Y-%m-%d").date() if isinstance(rd, str) else rd
    except (TypeError, ValueError):
        return False
    return (date.today() - d).days <= days


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--record", required=True, help="review-record JSON")
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    cfg = load_config(Path(args.config)).get("dsgvo-ai-act-labeling", {})
    window = int(cfg.get("label_recheck_days", 365))

    try:
        rec = load_record(Path(args.record))
    except ValueError as e:
        print(json.dumps({"ok": False, "reason": "malformed_record", "detail": str(e)}))
        return 2
    ev_path = Path(rec["review_evidence_path"])
    if not ev_path.is_absolute():
        ev_path = Path(args.record).resolve().parent / ev_path

    checks = {
        "human_review_done": rec.get("review_decision") == "approved",
        "review_within_window": review_within_window(rec, window),
        "editorial_responsibility_named": bool(rec.get("editorial_responsibility_holder")),
        "evidence_intact": evidence_intact(ev_path),
    }
    exempt = all(checks.values())
    failing = [k for k, v in checks.items() if not v]
    print(json.dumps({
        "result": "EXEMPT" if exempt else "LABEL",
        "content_id": rec.get("content_id"),
        "reviewer": rec.get("reviewer"),
        "checks": checks,
        "failing_conjuncts": failing,
        "recheck_window_days": window,
    }, indent=2, ensure_ascii=False))
    return 0 if exempt else 1


if __name__ == "__main__":
    sys.exit(main())
