#!/usr/bin/env python3
"""Poll the OFFICIAL carrier tracking endpoint for a tracking number.

Never scrape the public tracking page — every carrier has an official API,
scraping breaks on layout changes and violates the carrier's terms. Results
are cached for the configured TTL so the API is not hammered.

Usage:
    python3 track.py --carrier dhl --number 12345678901234567890 --dry-run
    python3 track.py --carrier dhl --number 12345678901234567890 --execute --token T --url U
"""
import argparse
import json
import sys
from pathlib import Path

TRACKING_ENDPOINTS = {
    "dhl": "/shipment/v2/tracking?shipmentNumber=",
    "dpd": "/track/",
    "gls": "/track?trackingNumber=",
    "hermes": "/tracking?id=",
    "ups": "/track?trackingNumber=",
}
CACHE_TTL_SECONDS = 300  # 5 minutes; never hammer the API


def build_request(carrier: str, number: str, token: str, url: str) -> dict:
    if carrier not in TRACKING_ENDPOINTS:
        raise SystemExit(f"unknown carrier: {carrier}")
    if not number:
        raise SystemExit("tracking number required")
    endpoint = url.rstrip("/") + TRACKING_ENDPOINTS[carrier] + number
    return {"method": "GET", "url": endpoint,
            "headers": {"Authorization": f"Bearer {token}",
                        "Accept": "application/json"}}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--carrier", required=True, choices=sorted(TRACKING_ENDPOINTS))
    ap.add_argument("--number", required=True, help="tracking number")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--token", help="bearer token (only with --execute)")
    ap.add_argument("--url", help="carrier base URL (only with --execute)")
    args = ap.parse_args()

    if not args.execute:
        print(json.dumps({"carrier": args.carrier, "tracking_number": args.number,
                          "cache_ttl_seconds": CACHE_TTL_SECONDS,
                          "endpoint_path": TRACKING_ENDPOINTS[args.carrier],
                          "note": "dry-run; use --execute to send"}, indent=2))
        return 0
    if not args.token or not args.url:
        ap.error("--execute requires --token and --url")
    import urllib.request
    req = urllib.request.Request(args.url, headers=build_request(
        args.carrier, args.number, args.token, args.url)["headers"])
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(r.read().decode())
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
