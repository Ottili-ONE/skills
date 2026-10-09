#!/usr/bin/env python3
"""Poll the OFFICIAL carrier tracking endpoint for a tracking number.

Never scrape the public tracking page — every carrier has an official API,
scraping breaks on layout changes and violates the carrier's terms. Results
are cached for the configured TTL (default 300 s) so the API is not hammered.
The cache is a JSON file on disk; it is deterministic and survives restarts.

Usage:
    python3 track.py --carrier dhl --number 12345678901234567890 --dry-run
    python3 track.py --carrier dhl --number 12345678901234567890 --execute --token T --url U
    python3 track.py --carrier dhl --number 12345678901234567890 --cache-file /tmp/cache.json
"""
import argparse
import json
import sys
import time
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

# Official tracking endpoints are pinned in config/versions.json (verified
# against each carrier portal, retrieval 2026-10-09). Never scrape the public
# tracking page and never hardcode an endpoint.
_TRACKING_ENDPOINTS = load_config().get("carrier-apis-de", {}).get(
    "tracking_endpoints", {}).get("value", {
        "dhl": "/shipment/v2/tracking?shipmentNumber=",
        "dpd": "/track/",
        "gls": "/track?trackingNumber=",
        "hermes": "/tracking?id=",
        "ups": "/track?trackingNumber=",
    })
# 5 minutes; carriers rate-limit tracking aggressively. Read from config if
# present, otherwise this default.
_CACHE_TTL = load_config().get("carrier-apis-de", {}).get(
    "cache_ttl_seconds", {}).get("value", 300)


def cache_get(cache_file: str, carrier: str, number: str) -> dict | None:
    """Return a cached response if it is still fresh, else None."""
    if not cache_file:
        return None
    p = Path(cache_file)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    entry = data.get(f"{carrier}:{number}")
    if not entry:
        return None
    if time.time() - entry.get("ts", 0) > _CACHE_TTL:
        return None  # stale — re-poll
    return entry


def cache_put(cache_file: str, carrier: str, number: str, body: str) -> None:
    if not cache_file:
        return
    p = Path(cache_file)
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    data[f"{carrier}:{number}"] = {"ts": time.time(), "body": body}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def build_request(carrier: str, number: str, token: str, url: str) -> dict:
    if carrier not in _TRACKING_ENDPOINTS:
        raise SystemExit(f"unknown carrier: {carrier}")
    if not number:
        raise SystemExit("tracking number required")
    if not number.isdigit():
        raise SystemExit("tracking number must be numeric")
    endpoint = url.rstrip("/") + _TRACKING_ENDPOINTS[carrier] + number
    return {"method": "GET", "url": endpoint,
            "headers": {"Authorization": f"Bearer {token}",
                        "Accept": "application/json"}}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--carrier", required=True, choices=sorted(_TRACKING_ENDPOINTS))
    ap.add_argument("--number", required=True, help="tracking number")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--token", help="bearer token (only with --execute)")
    ap.add_argument("--url", help="carrier base URL (only with --execute)")
    ap.add_argument("--cache-file", help="JSON cache file for TTL caching")
    args = ap.parse_args()

    if args.carrier not in _TRACKING_ENDPOINTS:
        raise SystemExit(f"unknown carrier: {args.carrier}")
    if not args.number:
        raise SystemExit("tracking number required")
    if not args.number.isdigit():
        raise SystemExit("tracking number must be numeric")
    cached = cache_get(args.cache_file, args.carrier, args.number)
    if cached:
        print(json.dumps({"carrier": args.carrier, "tracking_number": args.number,
                          "cache_hit": True, "body": cached["body"]}, indent=2))
        return 0

    if not args.execute:
        print(json.dumps({"carrier": args.carrier, "tracking_number": args.number,
                          "cache_ttl_seconds": _CACHE_TTL,
                          "endpoint_path": _TRACKING_ENDPOINTS[args.carrier],
                          "cache_file": args.cache_file,
                          "note": "dry-run; use --execute to send"}, indent=2))
        return 0
    if not args.token or not args.url:
        ap.error("--execute requires --token and --url")
    import urllib.request
    req = urllib.request.Request(args.url, headers=build_request(
        args.carrier, args.number, args.token, args.url)["headers"])
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    cache_put(args.cache_file, args.carrier, args.number, body)
    print(json.dumps({"carrier": args.carrier, "tracking_number": args.number,
                      "cache_hit": False, "body": body}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
