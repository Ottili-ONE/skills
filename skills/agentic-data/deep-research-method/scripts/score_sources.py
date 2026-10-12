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
    if not path.is_file():
        raise SystemExit(f"ERROR: sources file not found: {path}")
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
    if not sources:
        print("FAIL: no sources in file", file=sys.stderr)
        return 1
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


def cmd_contradictions(sources: list[dict], pairs_path: Path, min_score: int) -> int:
    """Report contradictions between kept sources, weighted by quality.

    Reads a JSON list of {a, b, claim_a, claim_b} pairs. For each pair the
    higher-scoring source wins; equal-score pairs are unresolved.
    """
    try:
        pairs = json.loads(pairs_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"FAIL: contradictions file is not valid JSON: {e}", file=sys.stderr)
        return 2
    if not isinstance(pairs, list):
        print("FAIL: contradictions file must be a JSON list", file=sys.stderr)
        return 2
    by_url = {s.get("url"): s for s in sources}
    unresolved = 0
    for i, pair in enumerate(pairs):
        a = by_url.get(pair.get("a"))
        b = by_url.get(pair.get("b"))
        if a is None or b is None:
            print(f"FAIL: pair {i} cites an unknown source", file=sys.stderr)
            return 1
        sa, sb = score_source(a), score_source(b)
        if sa > sb:
            verdict = f"{pair.get('a')} wins (score {sa} > {sb})"
        elif sb > sa:
            verdict = f"{pair.get('b')} wins (score {sb} > {sa})"
        else:
            verdict = "UNRESOLVED: equal scores"
            unresolved += 1
        print(f"INFO: pair {i}: {pair.get('claim_a', '?')} vs {pair.get('claim_b', '?')} -> {verdict}", file=sys.stderr)
    if unresolved:
        print(f"FAIL: {unresolved} contradiction(s) unresolved", file=sys.stderr)
        return 1
    print(f"PASS: all {len(pairs)} contradictions resolved by quality weight", file=sys.stderr)
    return 0


def cmd_audit(sources: list[dict], claims_path: Path, min_score: int) -> int:
    raw = claims_path.read_text(encoding="utf-8").strip()
    if not raw:
        print("FAIL: claims file is empty", file=sys.stderr)
        return 1
    # Claims files are JSONL (one claim per line) or a single JSON array/object.
    # Try a single JSON document first; fall back to one JSON object per line.
    try:
        claims = json.loads(raw)
    except json.JSONDecodeError:
        try:
            claims = [json.loads(line) for line in raw.splitlines() if line.strip()]
        except json.JSONDecodeError as exc:
            print(f"FAIL: claims file is not valid JSON or JSONL: {exc}", file=sys.stderr)
            return 1
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


def cmd_cite(sources: list[dict], min_score: int) -> int:
    """Emit a citation block: one line per kept source, URL + retrieval date."""
    kept = [s for s in sources if score_source(s) >= min_score and s.get("url")]
    if not kept:
        print("FAIL: no kept sources to cite", file=sys.stderr)
        return 1
    for s in kept:
        ver = f" v={s['version']}" if s.get("version") else ""
        print(f'{s["url"]} retrieved={s.get("retrieved", "?")}{ver}', file=sys.stderr)
    print(f"PASS: {len(kept)} citation(s) emitted", file=sys.stderr)
    return 0


def cmd_fetch(sources: list[dict], min_score: int) -> int:
    """Dry-run the fetch list: every kept source's URL, in order, for curl."""
    urls = [s["url"] for s in sources if score_source(s) >= min_score and s.get("url")]
    if not urls:
        print("FAIL: no kept sources to fetch", file=sys.stderr)
        return 1
    for u in urls:
        print(u)
    print(f"PASS: {len(urls)} fetch URL(s)", file=sys.stderr)
    return 0



def staleness(sources: list[dict], question_date: str, max_age_days: int = 365) -> tuple[list[str], list[dict]]:
    """Flag sources whose retrieval date is older than max_age_days before question_date.

    Returns (failures, stale). A stale source is not discarded by score; it is
    flagged so the researcher re-fetches it. The question date is explicit
    because "today" is not a fact the script can know.
    """
    from datetime import date, datetime
    try:
        qd = datetime.strptime(question_date, "%Y-%m-%d").date()
    except ValueError:
        return [f"FAIL: invalid question date '{question_date}' (need YYYY-MM-DD)"], []
    failures: list[str] = []
    stale: list[dict] = []
    for i, s in enumerate(sources):
        try:
            rd = datetime.strptime(str(s.get("retrieved", "")), "%Y-%m-%d").date()
        except ValueError:
            continue  # validate_source already flags a missing/invalid date
        age = (qd - rd).days
        if age > max_age_days:
            stale.append({**s, "age_days": age})
            failures.append(
                f"FAIL: source {i} ({s.get('url', '?')}) retrieved {s['retrieved']}, "
                f"{age}d before question date {question_date} -- re-fetch"
            )
    return failures, stale

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("staleness")
    p.add_argument("sources", type=Path)
    p.add_argument("--question-date", required=True, help="YYYY-MM-DD the question is about")
    p.add_argument("--max-age-days", type=int, default=365)

    p = sub.add_parser("score")
    p.add_argument("sources", type=Path)
    p.add_argument("--min", type=int, default=MIN_SCORE)

    p = sub.add_parser("audit")
    p.add_argument("sources", type=Path)
    p.add_argument("claims", type=Path)
    p.add_argument("--min", type=int, default=MIN_SCORE)

    p = sub.add_parser("contradictions")
    p.add_argument("sources", type=Path)
    p.add_argument("pairs", type=Path)
    p.add_argument("--min", type=int, default=MIN_SCORE)

    p = sub.add_parser("cite")
    p.add_argument("sources", type=Path)
    p.add_argument("--min", type=int, default=MIN_SCORE)

    p = sub.add_parser("fetch")
    p.add_argument("sources", type=Path)
    p.add_argument("--min", type=int, default=MIN_SCORE)

    args = ap.parse_args()
    if args.cmd in ("score", "cite", "fetch") and not args.sources.is_file():
        print(f"FAIL: sources file not found: {args.sources}", file=sys.stderr)
        return 2
    sources = load_sources(args.sources)
    if args.cmd == "staleness":
        failures, stale = staleness(sources, args.question_date, args.max_age_days)
        for f in failures:
            print(f, file=sys.stderr)
        if failures:
            print(f"FAIL: {len(stale)} source(s) are stale and must be re-fetched", file=sys.stderr)
            return 1
        print(f"PASS: no source is older than {args.max_age_days}d before {args.question_date}", file=sys.stderr)
        return 0
    if args.cmd == "score":
        return cmd_score(sources, args.min)
    if args.cmd == "contradictions":
        return cmd_contradictions(sources, args.pairs, args.min)
    if args.cmd == "cite":
        return cmd_cite(sources, args.min)
    if args.cmd == "fetch":
        return cmd_fetch(sources, args.min)
    return cmd_audit(sources, args.claims, args.min)


if __name__ == "__main__":
    raise SystemExit(main())
