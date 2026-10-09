#!/usr/bin/env python3
"""Decide whether an AI system needs an EU AI Act Article 50 disclosure label.

Implements the classification decision tree: does the system use AI, is it
high-risk, does it fall under a transparency-only obligation? Emits a
machine-readable label with the human-review evidence status. Missing
evidence for a high-risk system is BLOCKING — never auto-approve.

Usage:
    python3 disclosure_label.py --system system.json --evidence evidence.json
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

# Article 50 EU AI Act (Regulation (EU) 2024/1689) — verified 2026-10-09.
# Transparency obligations for certain AI systems; high-risk systems
# additionally require human oversight under Art. 5(4).
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

# Human-review evidence retention is inherited from the gobd-archive GoBD
# retention class (label artefacts are business records under HGB/AO); the
# number is pinned in config, never hardcoded (R3 rule).
RETENTION_YEARS = int(load_config().get("dsgvo-ai-act-labeling", {}).get(
    "human_review_retention_years", {}).get("value", 10))

TRANSPARENCY_ONLY = {"chatbot", "emotion-recognition", "deep-fake", "biometric-categorization"}
HIGH_RISK_ARTICLE_6 = "Annex III high-risk (Art. 6)"


def classify(system: dict) -> dict:
    """Return a label dict; raise SystemExit on invalid input."""
    name = system.get("name")
    if not name:
        raise SystemExit("system name required")
    ai_type = system.get("ai_type", "")
    if not ai_type:
        raise SystemExit("ai_type required")
    human_review = system.get("human_review", {})
    reviewer = human_review.get("reviewer_id")
    reviewed_at = human_review.get("reviewed_at")
    evidence_path = human_review.get("evidence_path")

    # Gate 1: is it AI at all?
    if ai_type == "none":
        return {"system": name, "risk_class": "not-ai", "article_50_required": False,
                "human_review_status": "n/a", "label": "no-ai-act-scope"}

    # Gate 2: transparency-only (Art. 50(1)-(4) disclosure, no human oversight).
    if ai_type in TRANSPARENCY_ONLY:
        if not reviewer or not reviewed_at:
            raise SystemExit(f"transparency system '{name}' requires human-review evidence")
        return {"system": name, "risk_class": "transparency-only",
                "article_50_required": True, "article_50_paragraph": "1-4",
                "human_review_status": "approved" if evidence_path else "missing",
                "label": "article-50-disclosure"}

    # Gate 3: high-risk (Annex III / Art. 6) — human oversight mandatory (Art. 5(4)).
    if ai_type in ("high-risk", HIGH_RISK_ARTICLE_6):
        if not reviewer or not reviewed_at or not evidence_path:
            raise SystemExit(f"high-risk system '{name}' BLOCKING: human-review evidence missing")
        ev = Path(evidence_path)
        if not ev.is_file():
            raise SystemExit(f"high-risk system '{name}' BLOCKING: evidence file not found")
        digest = hashlib.sha256(ev.read_bytes()).hexdigest()
        return {"system": name, "risk_class": "high-risk",
                "article_50_required": True, "article_50_paragraph": "5",
                "human_review_status": "approved", "reviewer_id": reviewer,
                "reviewed_at": reviewed_at, "evidence_sha256": digest,
                "label": "article-50-disclosure-hr"}

    # Gate 4: general AI (Art. 95) — no disclosure, but document.
    return {"system": name, "risk_class": "general", "article_50_required": False,
            "human_review_status": "not-required", "label": "ai-act-general"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--system", required=True, help="JSON file with the system description")
    args = ap.parse_args()

    system = json.loads(Path(args.system).read_text(encoding="utf-8"))
    label = classify(system)
    print(json.dumps(label, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
