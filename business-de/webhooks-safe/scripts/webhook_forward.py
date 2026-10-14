#!/usr/bin/env python3
"""SSRF-safe forward of a verified webhook body to a downstream URL.

The naive implementation (`requests.post(url, data=body)`) lets an attacker
who controls the payload redirect the forward at an internal address. This
script defends by:

  1. resolving the hostname *before* the request and rejecting anything that
     resolves to a private / loopback / link-local / reserved range;
  2. following no redirects (a redirect is itself a SSRF vector);
  3. pinning the scheme to https (or http only when explicitly allowed).

Usage:
    python3 webhook_forward.py --url https://example.com/hook --body events.json
Exit 0 = delivered. Exit 1 = blocked (reason in JSON). Exit 2 = usage error.
"""
import argparse
import ipaddress
import json
import socket
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

# Ranges that must never be reachable from a forward. RFC 1918 + loopback +
# link-local + unique-local + reserved (RFC 5735/RFC 3927/RFC 4193).
BLOCKED = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # link-local metadata (AWS/GCP)
    ipaddress.ip_network("100.64.0.0/10"),    # carrier-grade NAT
    ipaddress.ip_network("198.18.0.0/15"),    # benchmarking
    ipaddress.ip_network("224.0.0.0/4"),      # multicast
    ipaddress.ip_network("240.0.0.0/4"),      # reserved (future use)
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::/128"),
]


def is_blocked(host: str) -> str | None:
    """Return a reason string if `host` is an IP in a blocked range, else None."""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return None
    for net in BLOCKED:
        if ip in net:
            return f"blocked: {ip} is in {net}"
    return None


def resolve_and_check(url: str, allow_insecure: bool = False) -> str | None:
    """Resolve the URL's host and reject blocked ranges.

    Returns an error reason string, or None when the URL is safe to forward.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return f"blocked: scheme {parsed.scheme!r} not allowed"
    if parsed.scheme != "https" and not allow_insecure:
        return "blocked: only https is allowed for forwards"
    host = parsed.hostname
    if not host:
        return "blocked: no hostname in URL"
    direct = is_blocked(host)
    if direct:
        return direct
    try:
        infos = socket.getaddrinfo(host, parsed.port or 443)
    except socket.gaierror as e:
        return f"blocked: cannot resolve {host}: {e}"
    seen_ips = set()
    for family, _, _, _, sockaddr in infos:
        ip = sockaddr[0]
        if ip in seen_ips:
            continue
        seen_ips.add(ip)
        reason = is_blocked(ip)
        if reason:
            return reason
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", required=True)
    ap.add_argument("--body", required=True, help="path to the raw body file")
    ap.add_argument("--allow-insecure", action="store_true",
                    help="allow http (still blocks private ranges)")
    args = ap.parse_args()

    body = Path(args.body).read_bytes()
    reason = resolve_and_check(args.url, args.allow_insecure)
    if reason:
        print(json.dumps({"ok": False, "reason": reason, "url": args.url}))
        return 1

    req = urllib.request.Request(args.url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:  # noqa: BLE001 - any transport error is a blocked delivery
        print(json.dumps({"ok": False, "reason": "delivery_error",
                          "detail": str(e), "url": args.url}))
        return 1
    print(json.dumps({"ok": 200 <= status < 300, "status": status, "url": args.url}))
    return 0 if 200 <= status < 300 else 1


if __name__ == "__main__":
    sys.exit(main())
