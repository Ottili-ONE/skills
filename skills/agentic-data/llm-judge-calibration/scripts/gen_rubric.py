#!/usr/bin/env python3
"""Generate a valid judge rubric YAML from a compact spec.

A rubric that fails `rubric_lint.py` cannot be calibrated. This script emits a
rubric that passes it, from a small JSON spec, so the calibration pipeline has a
deterministic starting point.

Usage:
    python3 scripts/gen_rubric.py --spec spec.json --out rubric.yaml

The spec is a JSON object with `rubric_id`, `scale` (e.g. "1-5") and `points`,
a list of {score, definition, example, anti_examples}. Fully offline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def _die(msg: str, code: int = 2) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return code


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", type=Path, required=True, help="JSON rubric spec")
    ap.add_argument("--out", type=Path, required=True, help="output YAML path")
    args = ap.parse_args()

    if not args.spec.is_file():
        return _die(f"spec file not found: {args.spec}")
    if args.out.exists():
        return _die(f"output file already exists: {args.out}")
    if yaml is None:
        return _die("PyYAML is required to emit rubrics")

    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _die(f"spec is not valid JSON: {exc}")
    if not isinstance(spec, dict) or "points" not in spec:
        return _die("spec must be a JSON object with a 'points' list")

    points = []
    for p in spec["points"]:
        if not isinstance(p, dict) or "score" not in p:
            return _die(f"point {p} has no 'score'")
        points.append({
            "score": int(p["score"]),
            "definition": str(p.get("definition", "")),
            "example": str(p.get("example", "")),
            "anti_examples": [str(a) for a in p.get("anti_examples", [])],
        })
    points.sort(key=lambda p: p["score"])

    rubric = {
        "rubric_id": str(spec.get("rubric_id", "rubric-v1")),
        "scale": str(spec.get("scale", "1-5")),
        "points": points,
    }
    args.out.write_text(yaml.safe_dump(rubric, sort_keys=False, allow_unicode=True),
                        encoding="utf-8")
    print(f"PASS: rubric written to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
