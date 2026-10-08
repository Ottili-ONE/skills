#!/usr/bin/env python3
"""Recommend the Factur-X / ZUGFeRD profile for a given context.

Usage:
    python3 profile_selector.py --context B2B --data full --recipient factur-x
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

PROFILES = {
    ("b2b", "full", "factur-x"): ("COMFORT", "EN 16931 default for B2B"),
    ("b2b", "basic", "zugferd-basic"): ("BASIC", "B2B with simplified line items"),
    ("b2g", "full", "xrechnung"): ("COMFORT", "B2G public tender"),
    ("b2g", "full", "extended"): ("EXTENDED", "B2G with sector extensions"),
    ("b2b", "full", "extended"): ("EXTENDED", "sector extensions required"),
    ("b2c", "minimal", "any"): ("MINIMUM", "rarely an e-invoice"),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--context", required=True,
                    choices=["b2b", "b2g", "b2c"])
    ap.add_argument("--data", required=True,
                    choices=["full", "basic", "minimal"])
    ap.add_argument("--recipient", required=True,
                    choices=["factur-x", "zugferd-basic", "xrechnung", "extended", "any"])
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    key = (args.context, args.data, args.recipient)
    profile, rationale = PROFILES.get(
        key, ("COMFORT", "default fallback"))
    pinned = load_config(Path(args.config))["xrechnung-zugferd"]

    missing = []
    if profile in ("COMFORT", "EXTENDED"):
        missing += ["BT-10 Leitweg-ID", "BT-14 issue date", "BT-20 payment terms",
                    "BG-19 tax split per rate"]
    if profile == "BASIC":
        missing += ["BT-14", "BT-20", "BT-17", "BT-18"]
    if profile == "MINIMUM":
        missing = ["BT-14", "BT-20"]

    print(json.dumps({
        "recommended_profile": profile,
        "rationale": rationale,
        "pinned_spec": pinned["en16931"]["version"],
        "missing_fields": missing,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
