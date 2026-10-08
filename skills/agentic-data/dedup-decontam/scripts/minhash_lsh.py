#!/usr/bin/env python3
"""MinHash + LSH near-duplicate detection. Offline, deterministic, seeded.

Machine-readable summary (counts) -> stdout; human detail (FAIL:/PASS:/WARN:/INFO:)
-> stderr. Exit 0 = ok; exit 1 = any FAIL.

Usage:
  python3 minhash_lsh.py --docs d1.txt d2.txt --threshold 0.8
  echo "hello world" | python3 minhash_lsh.py --stdin --threshold 0.8
"""
import argparse
import hashlib
import sys
from pathlib import Path

DEFAULT_K = 128
DEFAULT_W = 5  # shingle width
DEFAULT_THRESHOLD = 0.8
DEFAULT_SEED = 1
MIN_K = 64


def _hash_bytes(token: bytes, seed: int) -> int:
    h = hashlib.blake2b(token, digest_size=8, key=seed.to_bytes(4, "little"))
    return int.from_bytes(h.digest(), "big")


def shingles(text: str, w: int) -> set:
    chars = [c for c in text if c.isprintable() or c in "\n\t "]
    s = "".join(chars)
    if len(s) < w:
        return {s} if s else set()
    return {s[i : i + w] for i in range(len(s) - w + 1)}


def minhash(tokens: set, k: int, seed: int) -> list:
    if k < MIN_K:
        raise ValueError(f"k must be >= {MIN_K}, got {k}")
    out = []
    for i in range(k):
        best = None
        for t in tokens:
            v = _hash_bytes(t.encode("utf-8"), seed + i)
            if best is None or v < best:
                best = v
        out.append(best if best is not None else 0)
    return out


def bands_for(k: int, target: float):
    """Choose (b, r) so that t ~= (1/b)^(1/r)."""
    best = None
    for r in range(1, 17):
        if k % r:
            continue
        b = k // r
        t = (1.0 / b) ** (1.0 / r)
        if best is None or abs(t - target) < abs(best[0] - target):
            best = (t, b, r)
    return best[1], best[2]


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def lsh_candidates(sigs: dict, k: int, target: float):
    """Return (b, r, [(id_a, id_b)]) candidate pairs sharing an LSH bucket."""
    b, r = bands_for(k, target)
    buckets = {}
    for doc_id, sig in sigs.items():
        for band in range(b):
            bucket_key = tuple(sig[band * r : (band + 1) * r])
            buckets.setdefault(bucket_key, []).append(doc_id)
    seen = set()
    pairs = []
    for members in buckets.values():
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                pair = tuple(sorted((members[i], members[j])))
                if pair not in seen:
                    seen.add(pair)
                    pairs.append(pair)
    return b, r, pairs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--docs", nargs="+")
    src.add_argument("--stdin", action="store_true")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--k", type=int, default=DEFAULT_K)
    ap.add_argument("--w", type=int, default=DEFAULT_W)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args()

    if args.k < MIN_K:
        print(f"FAIL: k={args.k} below minimum {MIN_K}", file=sys.stderr)
        return 1

    docs = {}
    if args.stdin:
        docs["stdin"] = sys.stdin.read()
    else:
        for p in args.docs:
            try:
                docs[Path(p).name] = Path(p).read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                print(f"FAIL: cannot read {p}: {e}", file=sys.stderr)
                return 1

    sets = {}
    sigs = {}
    for name, text in docs.items():
        s = shingles(text, args.w)
        sets[name] = s
        sigs[name] = minhash(s, args.k, args.seed)

    b, r, pairs = lsh_candidates(sigs, args.k, args.threshold)
    print(f"INFO: k={args.k} w={args.w} bands={b} rows={r} target~{(1/b)**(1/r):.3f}")
    found = 0
    for a, b2 in pairs:
        j = jaccard(sets[a], sets[b2])
        if j >= args.threshold:
            found += 1
            print(f"NEARDUPE {a} {b2} jaccard={j:.3f}")
    print(f"pairs={len(pairs)} above_threshold={found}")
    if not pairs:
        print("PASS: no near-duplicates found", file=sys.stderr)
    else:
        print(f"PASS: {found} near-duplicate pair(s) found", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
