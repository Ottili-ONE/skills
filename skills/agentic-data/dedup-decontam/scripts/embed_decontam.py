#!/usr/bin/env python3
"""Embedding-based decontamination: cosine similarity between corpus and prompts.

Runs offline on precomputed embeddings. The embedding *model* must be the same
for corpus and prompts, and the threshold must be pinned per model
(see references/procedures.md §4) — it is a CLI argument, never baked into logic.

Embeddings are read as JSON lists-of-lists (or numpy .npy if numpy is installed).
No network, no model loading: you precompute the embeddings elsewhere and feed
them in. This keeps the skill deterministic and runnable in any environment.

Machine-readable summary -> stdout; human detail (FAIL:/PASS:/WARN:/INFO:) -> stderr.
Exit 0 = ok; exit 1 = any FAIL (leakage found).

Usage:
  python3 embed_decontam.py --docs docs.json --doc_ids doc_ids.json \
      --prompts prompts.json --prompt_ids prompt_ids.json \
      --threshold 0.92 --model all-MiniLM-L6-v2
"""
import argparse
import json
import math
import sys
from pathlib import Path

try:
    import numpy as np  # type: ignore
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

DEFAULT_THRESHOLD = 0.92


def _load_npy(path: str):
    if not _HAS_NUMPY:
        print("FAIL: numpy required to read .npy files (pip install numpy)", file=sys.stderr)
        return None
    return np.load(path)


def _load_json_list(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        print(f"FAIL: {path} is not a JSON array", file=sys.stderr)
        return None
    return data


def load_embeddings(path: str):
    """Return a list of float vectors, or None on failure."""
    if path.endswith(".npy"):
        arr = _load_npy(path)
        if arr is None:
            return None
        return [list(map(float, row)) for row in arr]
    data = _load_json_list(path)
    if data is None:
        return None
    return data


def load_ids(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        return [str(v) for v in data.values()]
    if isinstance(data, list):
        return [str(v) for v in data]
    print(f"FAIL: {path} is not a JSON object or array", file=sys.stderr)
    return []


def cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--docs", required=True, help="embeddings file (.json list-of-lists or .npy)")
    ap.add_argument("--doc_ids", required=True)
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--prompt_ids", required=True)
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--model", required=True, help="embedding model used; threshold is pinned to it")
    ap.add_argument("--manifest", default=None)
    args = ap.parse_args()

    if not (-1.0 <= args.threshold < 1.0):
        print(f"FAIL: --threshold must be in [-1, 1), got {args.threshold}", file=sys.stderr)
        return 1

    docs = load_embeddings(args.docs)
    prompts = load_embeddings(args.prompts)
    if docs is None or prompts is None:
        return 1
    doc_ids = load_ids(args.doc_ids)
    prompt_ids = load_ids(args.prompt_ids)
    if not doc_ids or not prompt_ids:
        return 1
    if len(docs) != len(doc_ids):
        print(f"FAIL: docs rows {len(docs)} != doc_ids {len(doc_ids)}", file=sys.stderr)
        return 1
    if len(prompts) != len(prompt_ids):
        print(f"FAIL: prompts rows {len(prompts)} != prompt_ids {len(prompt_ids)}", file=sys.stderr)
        return 1
    dim = len(docs[0]) if docs else 0
    if any(len(d) != dim for d in docs) or any(len(p) != dim for p in prompts):
        print(f"FAIL: embedding dimension mismatch", file=sys.stderr)
        return 1

    flagged = 0
    pairs = []
    for i, d in enumerate(docs):
        for j, p in enumerate(prompts):
            s = cosine(d, p)
            if s >= args.threshold:
                flagged += 1
                pairs.append({"doc": doc_ids[i], "prompt": prompt_ids[j],
                              "cosine": round(s, 4)})
                print(f"EMBEDFLAG {doc_ids[i]} {prompt_ids[j]} cosine={s:.4f}")

    print(f"docs={len(doc_ids)} prompts={len(prompt_ids)} flagged={flagged} "
          f"threshold={args.threshold} model={args.model} dim={dim}")
    if args.manifest:
        manifest = {"model": args.model, "threshold": args.threshold,
                    "dim": dim, "flagged": flagged, "pairs": pairs}
        with open(args.manifest, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, sort_keys=True)
        print(f"INFO: manifest written to {args.manifest}", file=sys.stderr)
    if flagged:
        print(f"FAIL: {flagged} document/prompt pair(s) exceed the embedding threshold",
              file=sys.stderr)
        return 1
    print("PASS: no embedding leakage above threshold", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
