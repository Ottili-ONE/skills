"""Regenerate deep-research-method test fixtures.

Kept semantics (mirroring the original scratch fixtures):
  good.jsonl        three high-quality sources, distinct upstreams, full provenance
  bad.jsonl         one sub-threshold blog and one source with an invalid date
  equal.jsonl       two equal-quality sources with NO upstream field, used by the
                    equal-scores-UNRESOLVED contradiction test
  single.jsonl      one kept source -> medium confidence
  shared.jsonl      two kept URLs sharing one upstream -> the fake middle
"""
from __future__ import annotations

import json
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
    {"url": "https://example-blog.example/post", "authority": 1, "recency": 1, "corroboration": 0,
     "retrieved": "2026-10-09", "version": "1"},
    {"url": "https://arxiv.org/abs/2110.14111", "authority": 3, "recency": 0, "corroboration": 0,
     "retrieved": "not-a-date"},
]

# No `upstream` field: the contradiction resolver falls back to the URL, so the
# two sources look like two upstreams and the pair is UNRESOLVED.
EQUAL = [
    {"url": "https://arxiv.org/abs/2212.08073", "authority": 3, "recency": 2, "corroboration": 3,
     "retrieved": "2026-10-09", "version": "v1"},
    {"url": "https://openai.com/index/evals/", "authority": 3, "recency": 2, "corroboration": 3,
     "retrieved": "2026-10-09", "version": "HEAD"},
]

SINGLE = [
    {"url": "https://arxiv.org/abs/2212.08073", "authority": 3, "recency": 2, "corroboration": 3,
     "retrieved": "2026-10-09", "version": "v1", "upstream": "https://arxiv.org/abs/2212.08073"},
]

SHARED = [
    {"url": "https://arxiv.org/abs/2212.08073", "authority": 3, "recency": 2, "corroboration": 3,
     "retrieved": "2026-10-09", "version": "v1", "upstream": "https://arxiv.org/abs/2212.08073"},
    {"url": "https://mirror.example.com/arxiv-2212.08073", "authority": 3, "recency": 2, "corroboration": 3,
     "retrieved": "2026-10-09", "version": "v1", "upstream": "https://arxiv.org/abs/2212.08073"},
]


def write(name: str, rows: list[dict]) -> None:
    (OUT / f"{name}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )
    print(f"{name}.jsonl: {len(rows)} source(s)")


def main() -> int:
    for name, rows in (("good", GOOD), ("bad", BAD), ("equal", EQUAL),
                       ("single", SINGLE), ("shared", SHARED)):
        write(name, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
