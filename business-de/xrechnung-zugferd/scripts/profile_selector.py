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
                    choices=["b2b","b2g","b2c"], type=str.lower)
    ap.add_argument("--data", required=True,
                    choices=["full","basic","minimal"], type=str.lower)
    ap.add_argument("--recipient", required=True,
                    choices=["factur-x","zugferd-basic","xrechnung","extended","any"], type=str.lower)
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    key = (args.context, args.data, args.recipient)
    profile, rationale = PROFILES.get(
        key, ("COMFORT", "default fallback"))
    pinned = load_config(Path(args.config))["xrechnung-zugferd"]

    # "missing_fields" = the BT-* that a COMFORT/EXTENDED invoice needs but this
    # profile does NOT require. BT-14 and BT-20 are mandatory in *every*
    # profile (verified 2026-10-09 against the KoSIT guidelines.json), so they are
    # never listed here.
    extra_for_comfort = ["BT-10 Leitweg-ID", "BT-17 payment due date",
                         "BT-18 payment account (IBAN)", "BT-19 tax amount per rate",
                         "BG-19 tax split per rate", "BT-15 delivery date (BASIC WL+)"]
    if profile == "MINIMUM":
        missing = list(extra_for_comfort)
    elif profile == "BASIC":
        missing = [x for x in extra_for_comfort if not x.startswith("BT-15")]
    elif profile == "BASIC WL":
        missing = [x for x in extra_for_comfort if not x.startswith("BT-15")]
    else:  # COMFORT / EXTENDED
        missing = []

    print(json.dumps({
        "recommended_profile": profile,
        "rationale": rationale,
        "pinned_spec": pinned["en16931"]["version"],
        "missing_fields": missing,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
