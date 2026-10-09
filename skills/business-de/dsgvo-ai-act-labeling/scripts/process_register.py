#!/usr/bin/env python3
"""Maintain the GDPR processing register (Art. 30 GDPR).

Reads a processing activity, classifies it, and appends an Art. 30 entry to
the register JSONL. Never edits an existing entry in place — the register is
append-only (GoBD immutability; see gobd-archive skill).

Usage:
    python3 process_register.py --activity activity.json --register out.jsonl
"""
import argparse
import json
import sys
from pathlib import Path

# Art. 30(1) GDPR mandatory fields. Missing fields block the entry.
REQUIRED_FIELDS = [
    "controller", "purpose", "data_subject_categories", "data_categories",
    "recipients", "retention_period", "security_measures",
]
# Art. 6 GDPR legal bases. Exactly one primary basis per activity.
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

# Retention is inherited from the gobd-archive GoBD retention class (label
# artefacts are business records under HGB/AO); pinned in config, never
# hardcoded (R3 rule).
RETENTION_YEARS = int(load_config().get("dsgvo-ai-act-labeling", {}).get(
    "human_review_retention_years", {}).get("value", 10))

LEGAL_BASES = {
    "art6_1a_consent": "Consent (Art. 6(1)(a))",
    "art6_1b_contract": "Contractual necessity (Art. 6(1)(b))",
    "art6_1c_legal": "Legal obligation (Art. 6(1)(c))",
    "art6_1d_vital": "Vital interests (Art. 6(1)(d))",
    "art6_1e_task": "Public task (Art. 6(1)(e))",
    "art6_1f_legit": "Legitimate interests (Art. 6(1)(f))",
}


def classify(activity: dict) -> dict:
    """Return the Art. 30 entry or raise SystemExit on invalid input."""
    missing = [f for f in REQUIRED_FIELDS if f not in activity]
    if missing:
        raise SystemExit(f"Art. 30 entry missing fields: {missing}")
    basis = activity.get("legal_basis", "")
    if basis not in LEGAL_BASES:
        raise SystemExit(f"unknown legal basis '{basis}'; choose from {sorted(LEGAL_BASES)}")
    has_personal = activity.get("personal_data", True)
    entry = {
        "personal_data": has_personal,
        "legal_basis": basis,
        "legal_basis_label": LEGAL_BASES[basis],
        "controller": activity["controller"],
        "purpose": activity["purpose"],
        "data_subject_categories": activity["data_subject_categories"],
        "data_categories": activity["data_categories"],
        "recipients": activity["recipients"],
        "retention_period": activity["retention_period"],
        "security_measures": activity["security_measures"],
        "recorded_at": activity.get("recorded_at"),
        "ai_act_gate": activity.get("ai_act_gate", "pending"),
    }
    if not has_personal:
        entry["note"] = "No personal data — GDPR processing register entry optional; recorded for traceability."
    return entry


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--activity", required=True, help="JSON file with the processing activity")
    ap.add_argument("--register", required=True, help="JSONL register file (append-only)")
    args = ap.parse_args()

    activity = json.loads(Path(args.activity).read_text(encoding="utf-8"))
    entry = classify(activity)
    reg = Path(args.register)
    reg.parent.mkdir(parents=True, exist_ok=True)
    with reg.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(json.dumps({"ok": True, "entry": entry, "register": str(reg)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
