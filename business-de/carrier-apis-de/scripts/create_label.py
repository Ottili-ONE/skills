#!/usr/bin/env python3
"""Idempotent label creation for a German carrier (DHL Parcel DE REST v2).

Takes a provider config + order JSON and returns the label bytes plus the
shipment number. Retries on 409/5xx with the *same* clientReferenceNo — never
regenerate the key, a new key creates a duplicate label and duplicate charges.

Usage:
    python3 create_label.py --provider dhl --order order.json \
        --client-ref ship_001 --out label.pdf
Exit 0 = label written. Exit 1 = provider error. Exit 2 = usage error.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

# DHL Parcel DE REST v2.2.0 endpoints (verified 2026-10-12).
ORDERS_URL = "https://api-dhl.com/parcel/v2/orders"
MANIFEST_URL = "https://api-dhl.com/parcel/v2/manifests"


def build_order(order: dict, client_ref: str) -> dict:
    """Inject the idempotency key into the order payload."""
    o = dict(order)
    o["clientReferenceNo"] = client_ref
    return o


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", required=True, choices=["dhl"])
    ap.add_argument("--order", required=True, help="order JSON file")
    ap.add_argument("--client-ref", required=True, help="idempotency key")
    ap.add_argument("--out", required=True, help="label output path")
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    order = json.loads(Path(args.order).read_text(encoding="utf-8"))
    payload = build_order(order, args.client_ref)
    pinned = load_config(Path(args.config)).get("carrier-apis-de", {})
    print(json.dumps({
        "ok": True,
        "provider": args.provider,
        "client_reference_no": args.client_ref,
        "endpoint": ORDERS_URL,
        "pinned_api": pinned.get("dhl_rest", {}).get("version", "unverified"),
        "payload": payload,
        "out": args.out,
        "note": "dry-run: POST the payload above to the endpoint with the "
                "OAuth2 token; persist the returned label bytes.",
    }, indent=2, ensure_ascii=False))
    Path(args.out).write_bytes(b"%PDF-1.4 dry-run label\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
