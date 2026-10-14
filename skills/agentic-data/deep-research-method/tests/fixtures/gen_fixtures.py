"""Regenerate deep-research-method test fixtures.

Every kept source carries url + retrieved (ISO date) + version + the three
quality axes (authority 0-4, recency 0-3, corroboration 0-3). The `upstream`
field is what the corroboration/confidence subcommands group by: two URLs that
share an upstream count as one source, which is the "fake middle" trap.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

OUT = Path(__file__).resolve().parent

GOOD = [
    {"url": "https://arxiv.org/abs/2212.08073", "authority": 3, "recency": 2, "corroboration": 3,
     "retrieved": "2026-10-09", "version": "v1", "upstream": "https://arxiv.org/abs/2212.08073"},
    {"url": "https://openai.com/index/evals/", "authority": 3, "recency": 3, "corroboration": 3,
     "retrieved": "2026-10-09", "version": "HEAD", "upstream": "https://openai.com/index/evals/"},
    {"url": "https://www.europa.eu/legal-summary/", "authority": 4, "recency": 3, "corroboration": 3,
     "retrieved": "2026-10-09", "version": "2026-01", "upstream": "https://www.europa.eu/legal-summary/"},
]

BAD = [
    {"url": "https://example.com/blog", "authority": 1, "recency": 0, "corroboration": 0,
     "retrieved": "2026-10-09", "version": "1"},
    {"url": "https://example.net/old", "authority": 1, "recency": 1, "corroboration": 0,
     "retrieved": "2026-10-09", "version": "1"},
]

# Two URLs, one upstream: the fake-middle pattern. Both kept (score 6), but
# they trace to a single upstream, so confidence is medium, not high.
EQUAL = [
    {"url": "https://arxiv.org/abs/2212.08073", "authority": 3, "recency": 2, "corroboration": 3,
     "retrieved": "2026-10-09", "version": "v1", "upstream": "https://arxiv.org/abs/2212.08073"},
    {"url": "https://mirror.example.com/arxiv-2212.08073", "authority": 3, "recency": 2, "corroboration": 3,
     "retrieved": "2026-10-09", "version": "v1", "upstream": "https://arxiv.org/abs/2212.08073"},
]

# A single-upstream fixture for the medium-confidence case.
SINGLE = [
    {"url": "https://arxiv.org/abs/2212.08073", "authority": 3, "recency": 2, "corroboration": 3,
     "retrieved": "2026-10-09", "version": "v1", "upstream": "https://arxiv.org/abs/2212.08073"},
]


def write(name: str, rows: list[dict]) -> None:
    (OUT / f"{name}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )
    print(f"{name}.jsonl: {len(rows)} source(s)")


def main() -> int:
    write("good", GOOD)
    write("bad", BAD)
    write("equal", EQUAL)
    write("single", SINGLE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
