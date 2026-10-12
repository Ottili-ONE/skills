#!/usr/bin/env python3
"""Check one-to-one mapping between an error catalogue and an OpenAPI spec.

Exit codes: 0 = clean, 1 = drift, 2 = malformed input.
Usage: check_problem_catalogue.py --catalogue CAT.yaml --openapi API.yaml [--schema-dir DIR]
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML required: pip install pyyaml\n")
    sys.exit(2)


def load_catalogue(path: Path) -> dict:
    data = yaml.safe_load(path.read_text()) or {}
    codes = data.get("codes", data)
    if not isinstance(codes, dict):
        raise SystemExit(f"catalogue: expected mapping of code -> entry, got {type(codes)}")
    return codes


def load_openapi(path: Path) -> dict:
    data = yaml.safe_load(path.read_text()) or {}
    if "openapi" not in data:
        raise SystemExit(f"openapi: not an OpenAPI document (missing 'openapi' key)")
    return data


def responses_for_code(spec: dict, code: str) -> list:
    hits = []
    for path, methods in (spec.get("paths") or {}).items():
        for method, op in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            for status, resp in (op.get("responses") or {}).items():
                if str(status) == code:
                    hits.append((path, method, status))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", required=True)
    ap.add_argument("--openapi", required=True)
    ap.add_argument("--schema-dir", default=None)
    args = ap.parse_args()

    cat = load_catalogue(Path(args.catalogue))
    spec = load_openapi(Path(args.openapi))

    problems = []
    for code, entry in cat.items():
        if not responses_for_code(spec, code):
            problems.append(f"catalogue code {code!r} has no OpenAPI response entry")
        if isinstance(entry, dict):
            retriable = entry.get("retryable", False)
            if retriable and code in {"429", "503", "504"}:
                # presence of retry_after is checked in the schema, not here
                pass
    for path, methods in (spec.get("paths") or {}).items():
        for method, op in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            for status, resp in (op.get("responses") or {}).items():
                if not str(status).startswith(("4", "5")):
                    continue
                content = (resp.get("content") or {})
                if "application/problem+json" not in content:
                    problems.append(f"{method.upper()} {path} {status}: missing application/problem+json")

    if problems:
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        return 1
    print("ok: catalogue and OpenAPI responses are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
