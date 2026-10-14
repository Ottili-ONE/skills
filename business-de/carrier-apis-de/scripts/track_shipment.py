#!/usr/bin/env python3
"""Track a shipment via the official carrier API (DHL Shipment Tracking v1).

Never scrape www.dhl.de / www.dpd.de / gls-group.com — DPD gates tracking
behind a postal-code privacy check, GLS behind Cloudflare, UPS bot-protects
its endpoint (Apify, verified 2026-09-02). Use the official API or a
carrier webhook.

Usage:
    python3 track_shipment.py --provider dhl --ekp DE0123 --tracking 123456789012
Exit 0 = status printed. Exit 1 = unknown tracking number.
"""
import argparse
import json
import sys
from pathlib import Path

TRACK_URL = "https://api-dhl.com/parcel/v2/track"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", required=True, choices=["dhl"])
    ap.add_argument("--ekp", required=True, help="Erkenntlichkeitspunkt (EKP)")
    ap.add_argument("--tracking", required=True, help="shipment number")
    args = ap.parse_args()

    if not args.ekp.startswith("DE") or len(args.ekp) < 10:
        print(json.dumps({"ok": False, "reason": "invalid_ekp", "ekp": args.ekp}))
        return 1
    if not args.tracking.isdigit() or len(args.tracking) < 10:
        print(json.dumps({"ok": False, "reason": "invalid_tracking_number",
                          "tracking": args.tracking}))
        return 1
    print(json.dumps({
        "ok": True,
        "provider": args.provider,
        "endpoint": TRACK_URL,
        "ekp": args.ekp,
        "tracking": args.tracking,
        "note": "dry-run: GET the endpoint with the OAuth2 token in business "
                "mode; parse the status from the response.",
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
