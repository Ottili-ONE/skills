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

def _validate(instance: object, schema: dict, path: str = "$") -> list[str]:
    """Minimal JSON Schema draft 2020-12 validator for the constraints this checker needs.

    Deliberately a subset: type, required, properties, items, enum, minimum,
    maximum, minLength, maxLength, format. Anything else is reported as unsupported
    rather than silently ignored, so a real schema cannot hide a constraint here.
    """
    errors: list[str] = []
    if not isinstance(schema, dict):
        return errors
    t = schema.get("type")
    if t == "object":
        if not isinstance(instance, dict):
            errors.append(f"{path}: expected object, got {type(instance).__name__}")
            return errors
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: missing required property {req!r}")
        for prop, subschema in (schema.get("properties") or {}).items():
            if prop in instance:
                errors.extend(_validate(instance[prop], subschema, f"{path}.{prop}"))
    elif t == "array":
        if not isinstance(instance, list):
            errors.append(f"{path}: expected array, got {type(instance).__name__}")
            return errors
        for i, item in enumerate(instance):
            errors.extend(_validate(item, schema.get("items", {}), f"{path}[{i}]"))
    elif t == "string":
        if not isinstance(instance, str):
            errors.append(f"{path}: expected string, got {type(instance).__name__}")
        else:
            if "minLength" in schema and len(instance) < schema["minLength"]:
                errors.append(f"{path}: string shorter than minLength {schema['minLength']}")
            if "maxLength" in schema and len(instance) > schema["maxLength"]:
                errors.append(f"{path}: string longer than maxLength {schema['maxLength']}")
            if schema.get("format") == "uri":
                from urllib.parse import urlparse
                parsed = urlparse(instance)
                if not parsed.scheme or not parsed.netloc:
                    errors.append(f"{path}: not a valid absolute URI: {instance!r}")
    elif t == "integer":
        if isinstance(instance, bool) or not isinstance(instance, int):
            errors.append(f"{path}: expected integer, got {type(instance).__name__}")
        else:
            if "minimum" in schema and instance < schema["minimum"]:
                errors.append(f"{path}: integer below minimum {schema['minimum']}")
            if "maximum" in schema and instance > schema["maximum"]:
                errors.append(f"{path}: integer above maximum {schema['maximum']}")
    elif t == "number":
        if isinstance(instance, bool) or not isinstance(instance, (int, float)):
            errors.append(f"{path}: expected number, got {type(instance).__name__}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {instance!r} not in enum {schema['enum']}")
    unsupported = set(schema) - {
        "type", "required", "properties", "items", "enum", "minimum", "maximum",
        "minLength", "maxLength", "format", "$id", "$schema", "title", "description"}
    if unsupported:
        errors.append(f"{path}: unsupported schema keywords {sorted(unsupported)} - "
                      f"this validator is a subset and would miss them")
    return errors


def _duplicate_keys(raw: str) -> list[str]:
    """Detect mapping keys duplicated inside the same mapping.

    yaml.safe_load keeps the *last* value and silently drops earlier entries, so a
    duplicated problem code looks like a normal code. Scope is the path of enclosing
    keys, so a nested ``status`` under ``user-not-found`` does not collide with the
    top-level ``status``.
    """
    # yaml.safe_load keeps the *last* value for a duplicated key and silently drops
    # the earlier entry, so a duplicated problem code looks like a normal code.
    # We re-read the raw file and report every key that appears more than once at
    # the same scope. When a duplicate is found the earlier occurrence's children
    # are discarded by the parser, so their scopes are cleared here too - otherwise
    # a nested key under the first occurrence would be reported as colliding with
    # the same nested key under the second occurrence, which is a false positive.
    seen: dict[tuple[str, ...], int] = {}
    path: list[str] = []  # enclosing keys at each indent level
    indents: list[int] = []  # indent of each enclosing key
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
            indents.pop()
            last_indent = indents[-1] if indents else -1
        last_indent = indent
        indents.append(indent)
        scope = tuple(path + [key])
        if scope in seen:
            dups.append(f"{key} (line {seen[scope]} and {lineno})")
            # the later occurrence supersedes the earlier one: drop scopes that are
            # the earlier occurrence itself or nested under it.
            for dead in [sc for sc in seen if sc == scope or sc[:len(scope)] == scope]:
                del seen[dead]
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
    if schema_dir is None:
        return
    for code, entry in codes.items():
        status = entry.get("status") if isinstance(entry, dict) else None
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
            for err in _validate(instance, schema, f"{code}"):
                problems.append(f"schema: {code}.example.json fails {code}.json: {err}")
            # RFC 9457: the `status` field MUST equal the HTTP status code. A problem
            # document whose `status` lies (200 in a 404 response) is the #1 client-parse
            # failure, so the example must carry the catalogue status, not a different one.
            inst_status = instance.get("status") if isinstance(instance, dict) else None
            if inst_status != status:
                problems.append(
                    f"schema: {code}.example.json status {inst_status!r} does not match "
                    f"catalogue status {status}")
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
