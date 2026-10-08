#!/usr/bin/env python3
"""Score and validate a deep-research source list.

Reads a JSONL file where each row is a candidate source with `url`, `authority`
(0-4), `recency` (0-3), `corroboration` (0-3), `retrieved` (ISO date) and
optional `version`. Computes the total score, flags sources below the minimum,
and reports coverage: every claim must cite a kept source.

Subcommands:
  score   <sources.jsonl>             print scored sources, exit 1 if any < min
  audit   <sources.jsonl> <claims.json> check every claim cites a kept source

Fully offline and deterministic. Machine-readable counts to stdout,
FAIL:/PASS:/INFO: detail to stderr.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MIN_SCORE = 6
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_sources(path: Path) -> list[dict]:
    rows: list[dict] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            print(f"FAIL: line {i} is not valid JSON: {exc}", file=sys.stderr)
            raise SystemExit(1)
    return rows


def score_source(s: dict) -> int:
    return int(s.get("authority", 0)) + int(s.get("recency", 0)) + int(s.get("corroboration", 0))


def validate_source(s: dict, idx: int) -> list[str]:
    failures: list[str] = []
    if not s.get("url"):
        failures.append(f"FAIL: source {idx} missing 'url'")
    if not s.get("retrieved") or not DATE_RE.match(str(s.get("retrieved", ""))):
        failures.append(f"FAIL: source {idx} missing or invalid 'retrieved' (ISO date required)")
    for field in ("authority", "recency", "corroboration"):
        v = s.get(field)
        if not isinstance(v, int) or v < 0:
            failures.append(f"FAIL: source {idx} '{field}' must be a non-negative int")
    return failures


def cmd_score(sources: list[dict], min_score: int) -> int:
    failures: list[str] = []
    kept = 0
    for i, s in enumerate(sources):
        failures += validate_source(s, i)
        total = score_source(s)
        s["_total"] = total
        if total >= min_score:
            kept += 1
        else:
            failures.append(f"FAIL: source {i} score {total} < {min_score} ({s.get('url', '?')})")
        print(f"INFO: source {i} score={total} kept={total >= min_score} {s.get('url', '?')}", file=sys.stderr)
    if failures:
        for f in failures:
            print(f, file=sys.stderr)
        print(f"FAIL: {len(failures)} source problem(s)", file=sys.stderr)
        return 1
    print(f"PASS: {kept}/{len(sources)} sources kept at >= {min_score}", file=sys.stderr)
    return 0


def cmd_audit(sources: list[dict], claims_path: Path, min_score: int) -> int:
    claims = json.loads(claims_path.read_text(encoding="utf-8"))
    kept_urls = {s["url"] for s in sources if score_source(s) >= min_score and s.get("url")}
    failures: list[str] = []
    claim_list = claims.get("claims", claims) if isinstance(claims, dict) else claims
    if not isinstance(claim_list, list):
        print("FAIL: claims file must contain a JSON list of claims", file=sys.stderr)
        return 1
    for i, c in enumerate(claim_list):
        cited = c.get("cites", [])
        if not cited:
            failures.append(f"FAIL: claim {i} cites no source: {str(c.get('text', ''))[:40]}")
            continue
        if not any(u in kept_urls for u in cited):
            failures.append(f"FAIL: claim {i} cites a source that was not kept: {cited}")
    if failures:
        for f in failures:
            print(f, file=sys.stderr)
        print(f"FAIL: {len(failures)} claim problem(s)", file=sys.stderr)
        return 1
    print(f"PASS: all {len(claim_list)} claims cite a kept source", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("score")
    p.add_argument("sources", type=Path)
    p.add_argument("--min", type=int, default=MIN_SCORE)

    p = sub.add_parser("audit")
    p.add_argument("sources", type=Path)
    p.add_argument("claims", type=Path)
    p.add_argument("--min", type=int, default=MIN_SCORE)

    args = ap.parse_args()
    sources = load_sources(args.sources)
    if args.cmd == "score":
        return cmd_score(sources, args.min)
    return cmd_audit(sources, args.claims, args.min)


if __name__ == "__main__":
    raise SystemExit(main())
