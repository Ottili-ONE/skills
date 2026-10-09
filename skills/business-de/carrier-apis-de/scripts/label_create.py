#!/usr/bin/env python3
"""Build (dry-run) or send (live) an idempotent carrier label request.

Every label request MUST carry a client-generated idempotency key. The key
is your own order/shipment reference and must be stable across retries. On a
duplicate key the carrier returns the existing label — never create a second.

Usage:
    python3 label_create.py --carrier dhl --ref ORD-12345 --dry-run
    python3 label_create.py --carrier ups --ref ORD-12345 --execute --token T --url U

Offline by default. --execute sends the request and needs --token/--url.
"""
import argparse
import json
import sys
from pathlib import Path

# Per-carrier idempotency field name (verified against each carrier portal,
# retrieval 2026-10-09; see references/SOURCES.md). Never assume one header.
IDEMPOTENCY_FIELD = {
    "dhl": "X-Request-ID",
    "dpd": "shipmentReferenceNumber",
    "gls": "labelId",
    "hermes": "correlationId",
    "ups": "X-Inbound-Idempotency-Key",
}
IDEMPOTENCY_IN_BODY = {"dpd", "gls", "hermes"}
REQUIRED_LABEL_FIELDS = ["recipient", "address", "parcel", "service"]


def build_envelope(carrier: str, ref: str, payload: dict) -> dict:
    """Return the HTTP request envelope for a label create."""
    if carrier not in IDEMPOTENCY_FIELD:
        raise SystemExit(f"unknown carrier: {carrier}")
    missing = [f for f in REQUIRED_LABEL_FIELDS if f not in payload]
    if missing:
        raise SystemExit(f"label payload missing fields: {missing}")
    field = IDEMPOTENCY_FIELD[carrier]
    headers = {"Content-Type": "application/json"}
    if carrier not in IDEMPOTENCY_IN_BODY:
        headers[field] = ref
        body = payload
    else:
        body = dict(payload)
        body[field] = ref
    return {"method": "POST", "headers": headers, "body": body}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--carrier", required=True, choices=sorted(IDEMPOTENCY_FIELD))
    ap.add_argument("--ref", required=True, help="client-generated idempotency key")
    ap.add_argument("--payload", help="JSON file with the label payload")
    ap.add_argument("--execute", action="store_true", help="send the request")
    ap.add_argument("--token", help="bearer token (only with --execute)")
    ap.add_argument("--url", help="carrier label endpoint (only with --execute)")
    args = ap.parse_args()

    payload = json.loads(Path(args.payload).read_text()) if args.payload else {
        "recipient": "Ottili GmbH", "address": {"street": "Musterstr. 1", "city": "Berlin",
        "plz": "10117", "country": "DE"}, "parcel": {"size": "M"}, "service": "standard"}
    env = build_envelope(args.carrier, args.ref, payload)

    if not args.execute:
        print(json.dumps({"carrier": args.carrier, "idempotency_key": args.ref,
                          "idempotency_field": IDEMPOTENCY_FIELD[args.carrier],
                          "request": env}, indent=2, ensure_ascii=False))
        return 0

    if not args.token or not args.url:
        ap.error("--execute requires --token and --url")
    import urllib.request
    env["headers"]["Authorization"] = f"Bearer {args.token}"
    data = json.dumps(env["body"]).encode()
    req = urllib.request.Request(args.url, data=data, headers=env["headers"], method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(r.read().decode())
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
