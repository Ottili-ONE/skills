#!/usr/bin/env python3
"""Check one-to-one mapping between an error catalogue and an OpenAPI spec.

Exit codes: 0 = clean, 1 = drift, 2 = malformed input.
Usage: check_problem_catalogue.py --catalogue CAT.yaml --openapi API.yaml [--schema-dir DIR]
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML required: pip install pyyaml\n")
    sys.exit(2)

try:
    import jsonschema
except ImportError:
    jsonschema = None


def _duplicate_keys(raw: str) -> list[str]:
    """Detect mapping keys duplicated inside the same mapping.

    yaml.safe_load keeps the *last* value and silently drops earlier entries, so a
    duplicated problem code looks like a normal code. Scope is the path of enclosing
    keys, so a nested ``status`` under ``user-not-found`` does not collide with the
    top-level ``status``.
    """
    seen: dict[tuple[str, ...], int] = {}
    path: list[str] = []  # enclosing keys at each indent level
    dups: list[str] = []
    last_indent = -1
    for lineno, line in enumerate(raw.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        m = re.match(r"^([A-Za-z0-9_.\-]+)\s*:", stripped)
        if not m:
            continue
        key = m.group(1)
        while path and indent <= last_indent:
            path.pop()
            last_indent -= 2
        last_indent = indent
        scope = tuple(path + [key])
        if scope in seen:
            dups.append(f"{key} (line {seen[scope]} and {lineno})")
        else:
            seen[scope] = lineno
        path.append(key)
    return dups


def load_catalogue(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    dups = _duplicate_keys(raw)
    if dups:
        raise SystemExit(f"catalogue: duplicate code(s) {sorted(set(dups))} - "
                         f"yaml.safe_load would silently drop the earlier entries")
    data = yaml.safe_load(raw) or {}
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



def validate_examples(codes: dict, schema_dir: Path | None, problems: list[str]) -> None:
    """Every catalogue code must have a schema file, and every example must validate."""
    if schema_dir is None or jsonschema is None:
        return
    for code in codes:
        schema_path = schema_dir / f"{code}.json"
        if not schema_path.is_file():
            problems.append(f"schema: no schema file for code {code!r} ({schema_path})")
            continue
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"schema: {code}.json is not valid JSON: {exc}")
            continue
        examples = schema_dir / f"{code}.example.json"
        if examples.is_file():
            try:
                instance = json.loads(examples.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                problems.append(f"schema: {code}.example.json is not valid JSON: {exc}")
                continue
            try:
                jsonschema.validate(instance=instance, schema=schema)
            except jsonschema.ValidationError as exc:
                problems.append(f"schema: {code}.example.json fails {code}.json: {exc.message}")
        else:
            problems.append(f"schema: no example file for code {code!r} ({examples})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", required=True)
    ap.add_argument("--openapi", required=True)
    ap.add_argument("--schema-dir", default=None)
    args = ap.parse_args()

    try:
        cat = load_catalogue(Path(args.catalogue))
        spec = load_openapi(Path(args.openapi))
    except (FileNotFoundError, IsADirectoryError) as exc:
        sys.stderr.write(f"malformed input: {exc}\n")
        return 2

    problems = []
    for code, entry in cat.items():
        status = entry.get("status") if isinstance(entry, dict) else None
        if status is None:
            problems.append(f"catalogue code {code!r} has no status")
            continue
        if not responses_for_code(spec, str(status)):
            problems.append(
                f"catalogue code {code!r} (status {status}) has no OpenAPI response entry")
        if isinstance(entry, dict) and entry.get("retryable"):
            if entry.get("retry_after") in (None, ""):
                problems.append(f"catalogue code {code!r} is retryable but has no retry_after")
    for path, methods in (spec.get("paths") or {}).items():
        for method, op in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            for status, resp in (op.get("responses") or {}).items():
                if not str(status).startswith(("4", "5")):
                    continue
                content = resp.get("content") or {}
                if "application/problem+json" not in content:
                    problems.append(f"{method.upper()} {path} {status}: missing application/problem+json")
    validate_examples(cat, Path(args.schema_dir) if args.schema_dir else None, problems)

    if problems:
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        return 1
    print("ok: catalogue and OpenAPI responses are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
