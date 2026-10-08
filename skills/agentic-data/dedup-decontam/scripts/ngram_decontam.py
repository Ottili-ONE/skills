#!/usr/bin/env python3
"""n-gram decontamination: detect test-set leakage between corpus and prompts.

Offline, deterministic. Machine-readable summary -> stdout; human detail
(FAIL:/PASS:/WARN:/INFO:) -> stderr. Exit 0 = ok; exit 1 = any FAIL.

Usage:
  python3 ngram_decontam.py --corpus doc1.txt doc2.txt \
      --prompts prompt1.txt prompt2.txt --n 13
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalize import normalize  # noqa: E402

DEFAULT_N = 13
LEAK_SAMPLE_LEN = 60


_GPT2_PAT = re.compile(
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z]+| ?[0-9]+| ?[^\sA-Za-z0-9]+|\s+(?!\S)|\s+"""
)


def tokenize_gpt2(text: str) -> list:
    """GPT-2 byte-level BPE-ish tokenization proxy (regex pre-tokenizer).

    This is the same regex GPT-2 uses for pre-tokenization. It is a *proxy* for
    the full BPE merge step: for decontamination what matters is that corpus and
    prompts go through the same pre-tokenizer, so an n-gram that appears in both
    is an n-gram that appears in both. If you have the real tokenizer, pass
    `--tokenize raw` on already-tokenized input instead.
    """
    return _GPT2_PAT.findall(text)


def ngrams(tokens: list, n: int) -> set:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def normalize(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\u200b", "").replace("\u200c", "")
    text = text.replace("\u200d", "")
    out = []
    for ch in text:
        if ch == "\r":
            continue
        if ord(ch) < 32 and ch not in "\n\t":
            continue
        out.append(ch)
    s = "".join(out)
    s = s.lower()
    return " ".join(s.split())



def main_args(argv=None) -> int:
    """Programmatic entry point: parse argv (or sys.argv[1:]) and run."""
    import sys as _sys
    old = _sys.argv
    _sys.argv = [old[0]] + list(argv if argv is not None else old[1:])
    try:
        return main()
    finally:
        _sys.argv = old


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", nargs="+", required=True)
    ap.add_argument("--prompts", nargs="+", required=True)
    ap.add_argument("--n", type=int, default=DEFAULT_N)
    ap.add_argument("--tokenize", choices=["gpt2", "raw"], default="gpt2")
    ap.add_argument("--manifest", default=None, help="write JSON manifest here")
    args = ap.parse_args()

    if args.n < 2:
        print("FAIL: --n must be >= 2", file=sys.stderr)
        return 1

    prompt_ngrams = set()
    for p in args.prompts:
        try:
            text = Path(p).read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"FAIL: cannot read prompt {p}: {e}", file=sys.stderr)
            return 1
        text = normalize(text)
        toks = tokenize_gpt2(text) if args.tokenize == "gpt2" else text.split()
        prompt_ngrams |= ngrams(toks, args.n)

    hits = 0
    flagged = 0
    per_doc = {}
    for c in args.corpus:
        try:
            text = Path(c).read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"FAIL: cannot read corpus {c}: {e}", file=sys.stderr)
            return 1
        text = normalize(text)
        toks = tokenize_gpt2(text) if args.tokenize == "gpt2" else text.split()
        doc_ngrams = ngrams(toks, args.n)
        leaked = doc_ngrams & prompt_ngrams
        if leaked:
            flagged += 1
            hits += len(leaked)
            sample = " ".join(sorted(leaked)[0])
            print(f"LEAK {Path(c).name}: {len(leaked)} n-gram(s), e.g. '{sample[:LEAK_SAMPLE_LEN]}'")
            per_doc[Path(c).name] = {"action": "flagged", "reason": "ngram_leak",
                                     "leaked_ngrams": len(leaked),
                                     "sample": sample[:LEAK_SAMPLE_LEN]}
        else:
            print(f"OK {Path(c).name}")
            per_doc[Path(c).name] = {"action": "kept", "reason": "clean", "leaked_ngrams": 0}

    print(f"corpus_docs={len(args.corpus)} prompt_ngrams={len(prompt_ngrams)} "
          f"flagged={flagged} leaked_ngrams={hits}")
    if args.manifest:
        manifest = {"n": args.n, "tokenize": args.tokenize,
                    "prompt_files": args.prompts, "corpus_files": args.corpus,
                    "prompt_ngrams": len(prompt_ngrams),
                    "flagged": flagged, "leaked_ngrams": hits, "per_doc": per_doc}
        with open(args.manifest, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, sort_keys=True)
        print(f"INFO: manifest written to {args.manifest}", file=sys.stderr)
    if flagged:
        print(f"FAIL: {flagged} document(s) leak test-set n-grams", file=sys.stderr)
        return 1
    print("PASS: no test-set n-gram leakage", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
