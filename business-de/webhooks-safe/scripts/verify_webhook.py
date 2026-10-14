#!/usr/bin/env python3
"""Verify the HMAC signature of an inbound webhook body.

Providers send the signature in a request header. This script computes the
expected HMAC over the *raw* body bytes (not a re-serialized copy) and compares
in constant time. A mismatch is a hard stop: the event is never processed.

Usage:
    python3 verify_webhook.py --provider stripe --secret shh_... \
        --header 'X-Signature: t=1700000000,v1=abc' --body events.json
    echo -n 'raw body' | python3 verify_webhook.py --provider github \
        --secret WEBHOOK_SECRET --header 'X-Hub-Signature-256: sha256=..'
Exit 0 = signature valid. Exit 1 = invalid. Exit 2 = usage error.
"""
import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402

# Header name + signing scheme per provider. The secret is supplied on the
# command line (never read from a file); the scheme comes from config.
PROVIDERS = {
    "stripe": {"header": "X-Signature", "scheme": "t=<ts>,v1=<mac>"},
    "github": {"header": "X-Hub-Signature-256", "scheme": "sha256=<mac>"},
    "meta": {"header": "X-Hub-Signature-256", "scheme": "sha256=<mac>"},
}


def parse_stripe(header: str) -> tuple[str, str]:
    """Stripe: `t=<unix_ts>,v1=<hex_hmac>`."""
    ts = mac = ""
    for part in header.split(","):
        if part.startswith("t="):
            ts = part[2:]
        elif part.startswith("v1="):
            mac = part[3:]
    if not ts or not mac:
        raise ValueError("malformed Stripe signature header")
    return ts, mac


def expected_stripe(secret: str, ts: str, body: bytes) -> str:
    return hmac.new(secret.encode(), f"{ts}.".encode() + body,
                    hashlib.sha256).hexdigest()


def expected_sha256(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", required=True, choices=sorted(PROVIDERS))
    ap.add_argument("--secret", required=True, help="provider webhook secret")
    ap.add_argument("--header", required=True, help="raw signature header value")
    ap.add_argument("--body", help="path to the raw body file (default: stdin)")
    ap.add_argument("--config", default="config/versions.json")
    args = ap.parse_args()

    body = Path(args.body).read_bytes() if args.body else sys.stdin.buffer.read()
    cfg = load_config(Path(args.config)).get("webhooks-safe", {})
    replay_window = int(cfg.get("replay_window_minutes", 5))

    info = PROVIDERS[args.provider]
    try:
        if args.provider == "stripe":
            ts, mac = parse_stripe(args.header)
            expected = expected_stripe(args.secret, ts, body)
            # Reject a timestamp outside the replay window before comparing.
            import time
            now = int(time.time())
            if abs(now - int(ts)) > replay_window * 60:
                print(json.dumps({"ok": False, "reason": "stale_timestamp",
                                  "ts": ts, "now": now,
                                  "window_minutes": replay_window}))
                return 1
        else:
            mac = args.header.split("=", 1)[1] if "=" in args.header else ""
            expected = expected_sha256(args.secret, body)
    except (ValueError, IndexError) as e:
        print(json.dumps({"ok": False, "reason": "malformed_header", "detail": str(e)}))
        return 1

    if not mac:
        print(json.dumps({"ok": False, "reason": "no_signature"}))
        return 1

    valid = hmac.compare_digest(mac, expected)
    print(json.dumps({"ok": valid, "provider": args.provider,
                      "header": info["header"]}))
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
