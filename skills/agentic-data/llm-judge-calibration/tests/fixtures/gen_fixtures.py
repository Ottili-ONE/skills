"""Regenerate the llm-judge-calibration test fixtures.

Every fixture carries 30 items (the skill's minimum calibration-set size) so the
default --min-items=30 is satisfiable. Scores are integers in 1..5; the gold
label is the median of the scores. Fully deterministic (no RNG, no network).

The baseline fixture deliberately shares the same ids as `high.jsonl` but
shifts every score up by one, so a drift comparison against it is non-zero.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

HIGH = [(5, 5, 5), (4, 4, 4), (3, 3, 3), (2, 2, 2), (1, 1, 1)]
LOW = [(5, 1, 3), (4, 2, 1), (3, 5, 2), (2, 4, 1), (1, 3, 5)]
BIASED = [(5, 4, 4), (4, 3, 3), (3, 2, 2), (2, 1, 1), (1, 1, 1)]
# baseline: same ids as high, scores shifted +1 (clamped at 5) -> mean 4.0
BASELINE = [(5, 5, 5), (5, 5, 5), (4, 4, 4), (3, 3, 3), (2, 2, 2)]


def median(scores: list[int]) -> int:
    s = sorted(scores)
    n = len(s)
    return s[n // 2] if n % 2 else s[n // 2 - 1]


def write(name: str, rows: list[tuple[int, int, int]], id_prefix: str | None = None) -> None:
    items = []
    for i, sc in enumerate(rows):
        prefix = id_prefix or name
        items.append({"id": f"{prefix}-{i:02d}", "scores": list(sc), "gold": median(list(sc))})
    (OUT / f"{name}.jsonl").write_text(
        "".join(json.dumps(it, ensure_ascii=False) + "\n" for it in items), encoding="utf-8"
    )
    print(f"{name}.jsonl: {len(items)} items")


def main() -> int:
    for name, pattern in (("high", HIGH), ("low", LOW), ("biased", BIASED)):
        write(name, pattern * 6)
    # baseline reuses the high ids so the drift id-alignment check passes
    write("baseline", BASELINE * 6, id_prefix="high")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
