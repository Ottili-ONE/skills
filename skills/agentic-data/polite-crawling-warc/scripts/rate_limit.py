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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crawl-delay", type=float, default=None)
    ap.add_argument("--request-rate", type=float, default=None)
    ap.add_argument("--once", action="store_true", help="wait once, then exit")
    ap.add_argument("--n", type=int, default=1, help="number of waits (with --once)")
    args = ap.parse_args()

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
