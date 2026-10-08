#!/usr/bin/env python3
"""Planted-item test for the dedup-decontam pipeline.

Generates a corpus with 5 exact duplicates and 5 near-duplicates (Jaccard ~0.85),
runs the detectors, and reports pass/fail against the acceptance criteria:
5/5 exact found, >=4/5 near found.

Usage:
  python3 plant_test.py --out /tmp/corpus
  python3 plant_test.py --out /tmp/corpus --seed 7
"""
import argparse
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from minhash_lsh import shingles, minhash, jaccard  # noqa: E402

N_EXACT = 5
N_NEAR = 5
TARGET_JACCARD = 0.85
W = 5
K = 128
SEED = 1


def _random_words(rng, n):
    return " ".join("".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(5)) for _ in range(n))


def _mutate(text: str, rng, target_jaccard: float) -> str:
    words = text.split()
    keep = int(round(len(words) * target_jaccard))
    keep = max(1, keep)
    head = words[:keep]
    tail = words[keep:]
    new_tail = [w for w in tail if rng.random() > 0.5]
    new_tail += [_random_words(rng, 1) for _ in range(max(1, len(tail) - len(new_tail)))]
    rng.shuffle(new_tail)
    return " ".join(head + new_tail)


def build_corpus(out_dir: Path, seed: int) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    base = [_random_words(rng, 40) for _ in range(10)]
    for i, b in enumerate(base):
        (out_dir / f"base_{i}.txt").write_text(b, encoding="utf-8")

    exact = []
    for i in range(N_EXACT):
        name = f"exact_{i}.txt"
        (out_dir / name).write_text(base[i], encoding="utf-8")
        exact.append(name)

    near = []
    for i in range(N_NEAR):
        name = f"near_{i}.txt"
        mutated = _mutate(base[i + 5], rng, TARGET_JACCARD)
        (out_dir / name).write_text(mutated, encoding="utf-8")
        near.append(name)

    return {"base": [f"base_{i}.txt" for i in range(10)], "exact": exact, "near": near}


def run(out_dir: Path, seed: int) -> tuple[int, int, int]:
    info = build_corpus(out_dir, seed)
    docs = {}
    for name in info["base"] + info["exact"] + info["near"]:
        docs[name] = (out_dir / name).read_text(encoding="utf-8", errors="replace")

    sets = {n: shingles(t, W) for n, t in docs.items()}
    sigs = {n: minhash(s, K, SEED) for n, s in sets.items()}

    from minhash_lsh import lsh_candidates
    b, r, pairs = lsh_candidates(sigs, K, 0.8)

    exact_found = 0
    near_found = 0
    for a, b2 in pairs:
        j = jaccard(sets[a], sets[b2])
        if j < 0.8:
            continue
        # classify
        base_set = set(info["base"])
        exact_set = set(info["exact"])
        near_set = set(info["near"])
        if a in exact_set and b2 in base_set:
            exact_found += 1
        elif b2 in exact_set and a in base_set:
            exact_found += 1
        elif a in near_set or b2 in near_set:
            near_found += 1

    return exact_found, near_found, len(pairs)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    exact_found, near_found, pairs = run(Path(args.out), args.seed)
    exact_ok = exact_found == N_EXACT
    near_ok = near_found >= N_NEAR
    print(f"INFO: exact_found={exact_found}/{N_EXACT} near_found={near_found}/{N_NEAR} pairs={pairs}")
    if exact_ok and near_ok:
        print("PASS: planted-item test passed", file=sys.stderr)
        return 0
    print(f"FAIL: planted-item test failed (exact={exact_ok} near={near_ok})", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
