#!/usr/bin/env python3
"""Token-bucket rate limiter with Crawl-delay / Request-rate support. Offline, deterministic.

Machine-readable summary -> stdout; human detail (FAIL:/PASS:/WARN:/INFO:) -> stderr.
Exit 0 = ok; exit 1 = policy violation that cannot be recovered.

Usage:
  python3 rate_limit.py --crawl-delay 5 --once
  python3 rate_limit.py --request-rate 0.33 --once
"""
import argparse
import sys
import time
from pathlib import Path

DEFAULT_CRAWL_DELAY = 3.0
DEFAULT_REQUEST_RATE = 0.33


class RateLimiter:
    """Token bucket: `rate` tokens/s, burst of 1. `wait()` blocks until a token exists."""

    def __init__(self, rate: float = DEFAULT_REQUEST_RATE, crawl_delay: float | None = None):
        if crawl_delay is not None:
            rate = 1.0 / crawl_delay
        if rate <= 0:
            raise ValueError("rate must be > 0")
        self.rate = rate
        self.burst = 1.0
        self.tokens = self.burst
        self.last = time.monotonic()

    def wait(self) -> float:
        """Block until a token is available; return the seconds actually slept."""
        while True:
            now = time.monotonic()
            elapsed = now - self.last
            self.last = now
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return 0.0
            deficit = 1.0 - self.tokens
            sleep_for = deficit / self.rate
            time.sleep(sleep_for)
            return sleep_for


def cmd_check(log_path: Path, crawl_delay: float) -> int:
    """Audit a request log against the Crawl-delay policy.

    Reads a log of request timestamps (one ISO-8601 timestamp per line) and
    reports the measured rate and the worst gap. A measured rate above the
    policy is a FAIL, not a WARN: it is the difference between a polite
    crawler and a banned one. Fully offline.
    """
    from datetime import datetime
    if not log_path.is_file():
        print(f"FAIL: request log not found: {log_path}", file=sys.stderr)
        return 2
    times: list[float] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            times.append(datetime.fromisoformat(line.replace("Z", "+00:00")).timestamp())
        except ValueError:
            print(f"FAIL: bad timestamp line: {line!r}", file=sys.stderr)
            return 1
    if len(times) < 2:
        print("FAIL: need at least 2 timestamps to measure a rate", file=sys.stderr)
        return 1
    times.sort()
    gaps = [b - a for a, b in zip(times, times[1:])]
    worst = min(gaps)
    measured = 1.0 / (sum(gaps) / len(gaps)) if gaps else 0.0
    policy = 1.0 / crawl_delay if crawl_delay > 0 else float("inf")
    if worst < crawl_delay - 1e-6:
        print(f"FAIL: measured gap {worst:.3f}s < Crawl-delay {crawl_delay}s "
              f"({len(times)} requests) -- you are hammering the site",
              file=sys.stderr)
        return 1
    print(f"PASS: {len(times)} requests, worst gap {worst:.3f}s >= "
          f"Crawl-delay {crawl_delay}s, measured {measured:.3f} req/s <= policy {policy:.3f} req/s",
          file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crawl-delay", type=float, default=None)
    ap.add_argument("--request-rate", type=float, default=None)
    ap.add_argument("--once", action="store_true", help="wait once, then exit")
    ap.add_argument("--n", type=int, default=1, help="number of waits (with --once)")
    ap.add_argument("--check", metavar="LOG", type=Path,
                    help="audit a request log against --crawl-delay")
    args = ap.parse_args()

    if args.check is not None:
        if args.crawl_delay is None:
            print("FAIL: --check requires --crawl-delay", file=sys.stderr)
            return 2
        return cmd_check(args.check, args.crawl_delay)

    if args.crawl_delay is None and args.request_rate is None:
        print(f"WARN: no rate given, using default crawl-delay {DEFAULT_CRAWL_DELAY}s",
              file=sys.stderr)
        rl = RateLimiter(crawl_delay=DEFAULT_CRAWL_DELAY)
    elif args.crawl_delay is not None:
        rl = RateLimiter(crawl_delay=args.crawl_delay)
    else:
        rl = RateLimiter(rate=args.request_rate)

    total = 0.0
    for _ in range(args.n):
        total += rl.wait()
    print(f"rate={rl.rate:.3f}/s waits={args.n} total_sleep={total:.3f}s")
    print("PASS: rate limiter ran", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
