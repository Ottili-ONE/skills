#!/usr/bin/env python3
"""Deterministic text normalization + exact-dedup hashing for dedup-decontam.

Every comparison in the pipeline runs on the output of `normalize()`. Two documents
that differ only in BOM, zero-width chars, \r, case, or whitespace collapse to the
same SHA-256 and are treated as exact duplicates.

Machine-readable summary -> stdout; human detail (FAIL:/PASS:/WARN:/INFO:) -> stderr.
Exit 0 = ok; exit 1 = any FAIL.

Usage:
  python3 normalize.py --check a.txt b.txt     # exit 0 if identical after normalize
  echo "  Hello  " | python3 normalize.py --stdin
"""
import argparse
import hashlib
import sys


def normalize(text: str, lowercase: bool = True) -> str:
    """Canonical form: strip BOM/ZWJ/control, drop \r, lowercase, collapse whitespace."""
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
    if lowercase:
        s = s.lower()
    return " ".join(s.split())


def sha256_normalized(text: str, lowercase: bool = True) -> str:
    """Hex SHA-256 of the normalized bytes — the exact-dedup key."""
    return hashlib.sha256(normalize(text, lowercase).encode("utf-8")).hexdigest()


def exact_duplicates(paths: list[str]) -> dict:
    """Return {sha: [paths]} for hashes seen more than once."""
    seen: dict[str, list[str]] = {}
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as e:
            print(f"FAIL: cannot read {p}: {e}", file=sys.stderr)
            return {}
        seen.setdefault(sha256_normalized(text), []).append(p)
    return {h: ps for h, ps in seen.items() if len(ps) > 1}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", nargs="+", help="files to compare; exit 0 iff all normalize identically")
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--no-lowercase", action="store_true", help="skip lowercasing (use for code)")
    args = ap.parse_args()

    if args.check:
        texts = []
        for p in args.check:
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as fh:
                    texts.append(normalize(fh.read(), not args.no_lowercase))
            except OSError as e:
                print(f"FAIL: cannot read {p}: {e}", file=sys.stderr)
                return 1
        same = all(t == texts[0] for t in texts[1:])
        dig = sha256_normalized(texts[0], not args.no_lowercase)
        print(f"identical={str(same).lower()} sha256={dig} files={len(args.check)}")
        if same:
            print("PASS: all files normalize identically", file=sys.stderr)
            return 0
        print("FAIL: files differ after normalization", file=sys.stderr)
        return 1

    if args.stdin:
        text = sys.stdin.read()
        print(normalize(text, not args.no_lowercase))
        print("PASS: normalized", file=sys.stderr)
        return 0

    ap.error("--check or --stdin is required")
    return 2


if __name__ == "__main__":
    sys.exit(main())
