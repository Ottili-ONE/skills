#!/usr/bin/env python3
"""Emit and validate the structured browser hand-off summary.

Machine-readable summary -> stdout; human detail (FAIL:/PASS:/WARN:/INFO:) -> stderr.
Exit 0 = ok; exit 1 = schema violation.

Usage:
  python3 handoff.py --task "scrape table" --url https://x --title "T" \
      --field heading="Getting Started" --locator h1 \
      --out summary.json
  python3 handoff.py --validate summary.json        # check an existing file
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = ["task", "url", "title", "ended_at", "locator_strings",
            "key_fields", "evidence", "flags", "context_closed"]


def build(args) -> dict:
    """Build the hand-off summary. Returns a dict, or an empty dict carrying
    ``_error`` when the arguments are inconsistent -- never ``None``.

    Returning ``None`` was a latent bug: the CLI wrapper checked the return
    value, but callers that use ``build()`` directly (and every test that
    imports the module) passed the result straight to ``validate()``, which
    then crashed with ``TypeError: argument of type 'NoneType' is not
    iterable``. The empty-dict-with-error contract is the same one
    ``resume_state.load()`` uses and keeps the failure explicit.
    """
    if len(args.locator) != len(args.field):
        print(f"FAIL: need one --locator per --field "
              f"({len(args.locator)} locators for {len(args.field)} fields)",
              file=sys.stderr)
        return {"_error": "locator/field count mismatch"}
    fields = {}
    locators = []
    evidence = []
    for kv, loc in zip(args.field, args.locator or [None] * len(args.field)):
        if "=" not in kv:
            print(f"FAIL: --field must be name=value, got {kv!r}", file=sys.stderr)
            return {"_error": f"bad --field {kv!r}"}
        name, _, value = kv.partition("=")
        fields[name] = value
        locators.append(loc)
        evidence.append({"field": name, "value": value, "locator": loc})
    summary = {
        "task": args.task,
        "url": args.url,
        "title": args.title,
        "ended_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "locator_strings": locators,
        "key_fields": fields,
        "evidence": evidence,
        "flags": [],
        "context_closed": True,
    }
    return summary


def validate(summary: dict) -> list[str]:
    """Validate a hand-off summary. Returns a list of error strings.

    Tolerates ``None`` and summaries carrying ``_error`` (both are schema
    violations, never crashes) so the function is safe to call on the return
    value of ``build()`` without a null check.
    """
    if summary is None:
        return ["summary is None (build() failed)"]
    if isinstance(summary, dict) and summary.get("_error"):
        return [f"build failed: {summary['_error']}"]
    errors = []
    for k in REQUIRED:
        if k not in summary:
            errors.append(f"missing required field {k}")
    if not isinstance(summary.get("locator_strings"), list) or not summary["locator_strings"]:
        errors.append("locator_strings must be a non-empty list")
    if not isinstance(summary.get("evidence"), list) or not summary["evidence"]:
        errors.append("evidence must be a non-empty list; every finding needs a locator")
    for e in summary.get("evidence", []):
        if not e.get("locator"):
            errors.append("evidence entry missing locator")
    if summary.get("context_closed") is not True:
        errors.append("context_closed must be true (asserted by the finally block)")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task")
    ap.add_argument("--url")
    ap.add_argument("--title")
    ap.add_argument("--field", action="append", default=[],
                    help="name=value; also becomes an evidence entry")
    ap.add_argument("--locator", action="append", default=[],
                    help="locator string per --field, in order")
    ap.add_argument("--out")
    ap.add_argument("--validate")
    args = ap.parse_args()

    if args.validate:
        try:
            summary = json.loads(Path(args.validate).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"FAIL: cannot read {args.validate}: {e}", file=sys.stderr)
            return 1
        errors = validate(summary)
    else:
        if not (args.task and args.url and args.title and args.field):
            ap.error("--task --url --title --field are required without --validate")
        summary = build(args)
        if summary is None:
            return 1
        errors = validate(summary)

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        print(f"FAIL: {len(errors)} schema problem(s)", file=sys.stderr)
        return 1

    if args.validate:
        print(f"PASS: {args.validate} conforms to the hand-off schema", file=sys.stderr)
        return 0

    text = json.dumps(summary, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"INFO: hand-off written to {args.out}", file=sys.stderr)
    print(text)
    print("PASS: hand-off conforms to the schema", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
