#!/usr/bin/env python3
"""Map a SKR03/SKR04 account number to its default tax key and journal structure.

Reads rates from config/versions.json (never hardcoded). Runnable offline.

Usage:
    python3 map_skr.py --account 4000 [--skr 04]
    python3 map_skr.py --account 4100 --skr 03 --intra-eu
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from common import load_config  # noqa: E402

# Default Steuerschluessel per account, per Kontenrahmen.
ACCOUNT_TAX_KEYS = {
    "04": {"4000": "19", "4100": "00", "4200": "00", "4300": "07",
           "8000": "19", "8100": "19", "8200": "19", "8300": "07",
           "8400": "00", "8600": "19", "8900": "19"},
    "03": {"4000": "19", "4100": "00", "4200": "00", "4300": "07",
           "8000": "19", "8100": "19", "8200": "19", "8300": "07",
           "8400": "00", "8600": "19", "8900": "19"},
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--account", required=True, help="SKR account number")
    ap.add_argument("--skr", default="04", choices=["03", "04"])
    ap.add_argument("--intra-eu", action="store_true",
                    help="override to 0% for intra-EU supplies")
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    pinned = load_config(args.config)["skr-journal-mapping"]
    rates = pinned["ust_rates_2026"]
    account = args.account
    skr = args.skr

    if account not in ACCOUNT_TAX_KEYS.get(skr, {}):
        print(json.dumps({"ok": False, "error": "unknown account %s in SKR%s" % (account, skr)},
                         indent=2, ensure_ascii=False))
        return 1

    key = ACCOUNT_TAX_KEYS[skr][account]
    key_to_rate = {
        "19": rates["standard"], "07": rates["reduced"], "00": rates["zero"],
    }
    rate = key_to_rate.get(key)
    if rate is None:
        print(json.dumps({"ok": False, "error": "tax key %s not in config rates" % key},
                         indent=2, ensure_ascii=False))
        return 1

    override = None
    if args.intra_eu and key in ("19", "07"):
        key = "00"
        rate = rates["zero"]
        override = "intra-EU override applied (0%)"
    elif args.intra_eu and key == "00":
        override = "already 0% (intra-EU/export) - no override needed"

    result = {
        "ok": True,
        "kontenrahmen": "SKR%s" % skr,
        "account": account,
        "default_tax_key": key,
        "rate_percent": rate,
        "rates_from_config": rates,
        "override": override,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
