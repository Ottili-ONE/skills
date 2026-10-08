#!/usr/bin/env python3
"""Sanitize untrusted page text before it enters an LLM prompt.

Machine-readable summary (counts) goes to stdout; human detail (FAIL:/PASS:/WARN:/INFO:)
goes to stderr. Exit 0 = clean or warn-only; exit 1 = any FAIL.

Usage:
  python3 sanitize.py < input.txt            # stdin -> stdout
  python3 sanitize.py --check < input.txt    # exit 1 if any FAIL
  python3 sanitize.py --max 4000 < input.txt # truncate before scan
"""
import argparse
import re
import sys

MARKER_START = "BEGIN_UNTRUSTED_DATA"
MARKER_END = "END_UNTRUSTED_DATA"
DEFAULT_MAX = 8000

INSTRUCTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous\s+)?instructions?",
    r"system\s+override",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"you\s+are\s+now\s+(in\s+)?(developer\s+)?mode",
    r"disregard\s+(all\s+)?(previous\s+)?",
    r"forget\s+(everything|all)\s+(above|previous)",
    r"new\s+instructions?\s*:",
]

EXFIL_PATTERNS = [
    r"<img\s+src\s*=\s*[\"']https?://",
    r"fetch\(\s*[\"']https?://",
    r"new\s+WebSocket\(\s*[\"']wss?://",
    r"\bwebhook\b",
]

ENCODING_PATTERNS = [
    r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{40,}={0,2}(?![A-Za-z0-9+/=])",          # long base64
    r"\\u200[0-9a-fA-F]",                        # zero-width unicode
    r"\\color\{white\}",                         # KaTeX invisible text
    r"&#x200[0-9a-fA-F];",                       # invisible HTML entities
]


def _damerau_levenshtein(a: str, b: str, limit: int = 1) -> int:
    """Bounded Damerau-Levenshtein distance; returns > `limit` if it exceeds it.

    Counts substitution, insertion, deletion *and adjacent transposition* as one
    edit. The bound lets us short-circuit: most word pairs are far apart and we
    never build the full matrix. Verified against the OWASP typoglycemia example
    on 2026-10-08 (the example word `systme` is an adjacent-transposition of
    `system`, which a plain Levenshtein or anagram-only detector both miss).
    """
    if a == b:
        return 0
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur[j] = min(
                prev[j] + 1,          # deletion
                cur[j - 1] + 1,       # insertion
                prev[j - 1] + cost,   # substitution
            )
            if (
                i > 1
                and j > 1
                and ca == b[j - 2]
                and a[i - 2] == cb
                and cur[j] > prev[j - 2] + 1
            ):
                cur[j] = prev[j - 2] + 1  # adjacent transposition
        if min(cur) > limit:
            return limit + 1
        prev = cur
    return prev[len(b)] if prev[len(b)] <= limit else limit + 1


def is_typoglycemia(word: str, target: str) -> bool:
    """True if `word` is a typoglycemia-style scramble of `target`.

    Two routes, both from the OWASP LLM Prompt Injection Prevention Cheat Sheet
    (retrieved 2026-10-08):

    1. Anagram scramble with the first and last letter fixed (the classic
       `ignroe` -> `ignore` form).
    2. A single Damerau-Levenshtein edit with the first letter fixed, which also
       catches adjacent transpositions such as `systme` -> `system` and single
       substitutions such as `bpyass`-style slips.

    The first letter gate is what stops ordinary English words from colliding
    with the small target vocabulary.
    """
    word, target = word.lower(), target.lower()
    if len(word) < 4 or not target:
        return False
    if word == target:
        return False
    if word[0] != target[0]:
        return False
    if len(word) == len(target) and len(word) >= 4:
        if word[-1] == target[-1] and sorted(word[1:-1]) == sorted(target[1:-1]):
            return True
    if abs(len(word) - len(target)) <= 1 and _damerau_levenshtein(word, target, 1) <= 1:
        return True
    return False


TYPO_TARGETS = ["ignore", "instructions", "override", "bypass", "reveal", "prompt", "system"]


def sanitize(text: str, max_chars: int = DEFAULT_MAX) -> dict:
    """Return {clean, flags, truncated, length}."""
    flags = []
    truncated = False
    if len(text) > max_chars:
        text = text[:max_chars]
        truncated = True

    # Strip control chars and zero-width markers.
    cleaned = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
    cleaned = cleaned.replace(MARKER_START, "").replace(MARKER_END, "")

    for p in INSTRUCTION_PATTERNS:
        if re.search(p, cleaned, re.IGNORECASE):
            flags.append(f"instruction:{p}")
    for p in EXFIL_PATTERNS:
        if re.search(p, cleaned, re.IGNORECASE):
            flags.append(f"exfil:{p}")
    for p in ENCODING_PATTERNS:
        if re.search(p, cleaned):
            flags.append(f"encoding:{p}")
    words = re.findall(r"\b\w+\b", cleaned.lower())
    for w in words:
        for t in TYPO_TARGETS:
            if is_typoglycemia(w, t):
                flags.append(f"typoglycemia:{w}~{t}")
                break
    return {"clean": cleaned, "flags": sorted(set(flags)), "truncated": truncated, "length": len(cleaned)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="exit 1 on any FAIL")
    ap.add_argument("--max", type=int, default=DEFAULT_MAX, help=f"max chars before scan (default {DEFAULT_MAX})")
    args = ap.parse_args()
    data = sys.stdin.read()
    r = sanitize(data, args.max)
    # Machine-readable summary -> stdout.
    print(f"length={r['length']} truncated={str(r['truncated']).lower()} flags={len(r['flags'])}")
    # Human detail -> stderr.
    if r["truncated"]:
        print(f"WARN: input truncated to {args.max} chars", file=sys.stderr)
    for f in r["flags"]:
        print(f"FAIL: {f}", file=sys.stderr)
    if not r["flags"]:
        print("PASS: no injection indicators", file=sys.stderr)
    if args.check and r["flags"]:
        return 1
    # Quoted, safe output -> stdout.
    print(f"{MARKER_START}\n{r['clean']}\n{MARKER_END}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
