#!/usr/bin/env python3
"""Verify a webhook signature over the RAW body.

Never parse the body first and re-encode it — JSON re-encoding changes byte
order and every signature fails. Read the raw bytes. Always use
hmac.compare_digest (a plain == is a timing attack).

Usage:
    python3 verify.py --provider github --secret s --body body.json --sig 'sha256=abc'
"""
import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from common import load_config  # noqa: E402


def _replay_window(provider: str) -> int:
    """Replay window in seconds, pinned in config (never hardcoded)."""
    cfg = load_config().get("webhooks-safe", {})
    key = f"{provider}_replay_window_minutes"
    mins = cfg.get(key, {}).get("value", 5)
    return int(mins) * 60


REPLAY_WINDOW_SECONDS = {
    "stripe": _replay_window("stripe"),
    "github": _replay_window("github"),
    "paypal": _replay_window("paypal"),
    "twilio": _replay_window("twilio"),
}


def verify_github(secret: str, body: bytes, sig: str) -> bool:
    if not sig.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


def verify_stripe(secret: str, body: bytes, sig: str, now: int) -> bool:
    parts = dict(p.split("=", 1) for p in sig.split(",") if "=" in p)
    ts = int(parts.get("t", "0"))
    if abs(now - ts) > REPLAY_WINDOW_SECONDS["stripe"]:
        return False
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, parts.get("v1", ""))


def verify_paypal_twilio(secret: str, body: bytes, sig: str, now: int) -> bool:
    """HMAC-SHA256 over the raw body, hex digest, with a replay window.

    The exact PayPal/Twilio header layout could not be re-verified to a
    plain-text crawl (recorded in references/SOURCES.md as unverified), so
    this path is conservative: it checks the digest AND the replay window and
    refuses to verify when no timestamp is available. A provider whose scheme
    differs must be added explicitly, not silently passed.
    """
    if not sig:
        return False
    ts = None
    if "t=" in sig:
        try:
            ts = int(sig.split("t=", 1)[1].split(",", 1)[0])
        except ValueError:
            ts = None
    if ts is None:
        # No timestamp in the signature -> cannot bound the replay window.
        return False
    if abs(now - ts) > REPLAY_WINDOW_SECONDS["paypal"]:
        return False
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + body,
                        hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", required=True,
                    choices=["github", "stripe", "paypal", "twilio"])
    ap.add_argument("--secret", required=True)
    ap.add_argument("--body", required=True, help="file with the raw body bytes")
    ap.add_argument("--sig", required=True, help="signature header value")
    ap.add_argument("--now", type=int, default=0,
                    help="unix timestamp; REQUIRED for stripe/paypal/twilio "
                         "(0 = skip replay check, github only)")
    args = ap.parse_args()

    body = Path(args.body).read_bytes()
    if args.provider == "github":
        ok = verify_github(args.secret, body, args.sig)
    elif args.provider == "stripe":
        if not args.now:
            print(json.dumps({"ok": False,
                              "error": "--now is required for stripe: the replay "
                                       "window is enforced, not optional"},
                             indent=2), file=sys.stderr)
            return 2
        ok = verify_stripe(args.secret, body, args.sig, args.now)
    else:
        if not args.now:
            print(json.dumps({"ok": False,
                              "error": "--now is required for paypal/twilio: the "
                                       "replay window is enforced, not optional"},
                             indent=2), file=sys.stderr)
            return 2
        ok = verify_paypal_twilio(args.secret, body, args.sig, args.now)
    print(json.dumps({"provider": args.provider, "valid": ok}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
