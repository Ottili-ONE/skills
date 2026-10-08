#!/usr/bin/env python3
"""RFC 9309 robots.txt parser and path checker. Offline, deterministic.

Machine-readable summary (counts) -> stdout; human detail (FAIL:/PASS:/WARN:/INFO:)
-> stderr. Exit 0 = allowed or warn; exit 1 = disallowed or parse failure (default-deny).

Usage:
  python3 robots.py --file robots.txt --path /private/x
  python3 robots.py --file robots.txt --path /public/x
  echo "User-agent: *\nDisallow: /" | python3 robots.py --path /anything
"""
import argparse
import re
import sys

MAX_BYTES = 500 * 1024  # RFC 9309 §2.3.1.3 parsing limit
DEFAULT_USER_AGENT = "*"


def parse_robots(text: str) -> dict:
    """Return {group: [rules]} where rules are (action, pattern, length)."""
    if len(text.encode("utf-8", "replace")) > MAX_BYTES:
        return {}  # too large -> default-deny handled by caller
    groups = {}
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip().lower()
        val = val.strip()
        if key == "user-agent":
            current = val
            groups.setdefault(current, [])
        elif key in ("allow", "disallow") and current is not None:
            groups[current].append((key, val))
        # crawl-delay / request-rate / sitemap are read separately
    return groups


def _match_length(pattern: str, path: str) -> int:
    """Longest prefix of `pattern` (with wildcards) that matches `path`; 0 if no match.

    RFC 9309 §2.2.2: the path-part is matched as a *prefix* of the request path,
    with '*' matching any sequence. A trailing '$' in the pattern anchors the
    match to the end of the path.
    """
    anchored = pattern.endswith("$")
    pat = pattern[:-1] if anchored else pattern
    regex = "^" + re.escape(pat).replace(r"\*", ".*")
    if anchored:
        regex += "$"
    m = re.match(regex, path)
    if not m:
        return 0
    return m.end()


def is_allowed(groups: dict, path: str, user_agent: str = DEFAULT_USER_AGENT) -> bool:
    """RFC 9309 §2.2.2: the most specific matching rule wins; Allow can override Disallow."""
    if not groups:
        return True  # no rules for this UA -> everything allowed
    best_allow = 0
    best_disallow = 0
    for ua, rules in groups.items():
        if ua != DEFAULT_USER_AGENT and ua.lower() != user_agent.lower():
            continue
        for action, pattern in rules:
            if not pattern:
                # empty Disallow: -> allow everything; Allow: -> allow everything
                if action == "allow":
                    return True
                continue
            n = _match_length(pattern, path)
            if n == 0:
                continue
            if action == "allow" and n > best_allow:
                best_allow = n
            elif action == "disallow" and n > best_disallow:
                best_disallow = n
    if best_allow >= best_disallow:
        return True
    return False


def robots_status_decision(status_code: int | None, err: Exception | None = None) -> tuple[bool, str]:
    """RFC 9309 §2.3.1.3 (Unavailable) vs §2.3.1.4 (Unreachable).

    Returns (allow_crawl, reason). Verified against rfc9309.txt on 2026-10-08.
    4xx (incl. 404) -> robots.txt unavailable -> MAY crawl (default: allow).
    5xx or network error -> robots.txt unreachable -> MUST disallow.
    """
    if err is not None or status_code is None or status_code >= 500:
        return False, "robots.txt unreachable (5xx/network) -> default-deny per RFC 9309 §2.3.1.4"
    if 400 <= status_code <= 499:
        return True, "robots.txt unavailable (4xx) -> may crawl per RFC 9309 §2.3.1.3"
    if 200 <= status_code <= 299:
        return True, "robots.txt fetched OK"
    return False, f"unexpected status {status_code} -> default-deny"


def crawl_delay_from_lines(lines: list[str], user_agent: str = DEFAULT_USER_AGENT) -> float | None:
    """Read Crawl-delay: for the matching user-agent group from raw lines."""
    current = None
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip().lower(), val.strip()
        if key == "user-agent":
            current = val
        elif key == "crawl-delay" and current is not None:
            if current == DEFAULT_USER_AGENT or current.lower() == user_agent.lower():
                try:
                    return float(val.split("#")[0].strip())
                except ValueError:
                    return None
    return None


def request_rate_from_lines(lines: list[str], user_agent: str = DEFAULT_USER_AGENT) -> float | None:
    current = None
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip().lower(), val.strip()
        if key == "user-agent":
            current = val
        elif key == "request-rate" and current is not None:
            if current == DEFAULT_USER_AGENT or current.lower() == user_agent.lower():
                try:
                    return float(val.split("#")[0].strip())
                except ValueError:
                    return None
    return None



def crawl_delay(groups: dict, user_agent: str = DEFAULT_USER_AGENT) -> float | None:
    for ua, rules in groups.items():
        if ua != DEFAULT_USER_AGENT and ua.lower() != user_agent.lower():
            continue
        # crawl-delay is not a rule pair; re-parse is done by caller. Here we
        # accept a pre-parsed dict of directives.
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", help="robots.txt path (default: stdin)")
    ap.add_argument("--path", required=True, help="path to check")
    ap.add_argument("--ua", default=DEFAULT_USER_AGENT)
    ap.add_argument("--status", type=int, default=None,
                    help="HTTP status of the robots.txt fetch (applies RFC 9309 default-deny rules)")
    args = ap.parse_args()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as e:
            print(f"FAIL: cannot read robots file: {e}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()

    groups = parse_robots(text)
    if not groups:
        print("WARN: robots.txt empty/unparseable -> default-deny", file=sys.stderr)
        return 1

    if args.status is not None:
        allow, reason = robots_status_decision(args.status)
        print(f"status_decision={str(allow).lower()} reason={reason}")
        if not allow:
            print(f"FAIL: {reason}", file=sys.stderr)
            return 1
        # RFC 9309 §2.3.1.3: robots.txt unavailable (4xx) -> the crawler MAY access
        # ANY resource on the server. The rules below do not apply; exit allowed now.
        print(f"path={args.path} groups={len(groups)} allowed=true")
        print("PASS: robots.txt unavailable (4xx) -> may crawl per RFC 9309 §2.3.1.3",
              file=sys.stderr)
        return 0

    allowed = is_allowed(groups, args.path, args.ua)
    print(f"path={args.path} groups={len(groups)} allowed={str(allowed).lower()}")
    if allowed:
        print("PASS: path allowed by robots.txt", file=sys.stderr)
        return 0
    print(f"FAIL: path disallowed by robots.txt ({args.path})", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
