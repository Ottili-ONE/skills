#!/usr/bin/env python3
"""Validate an MCP server's server/discover response against the 2026-07-28 contract.

Reads a JSON document (file argument or stdin) describing a discover response and
checks the MUST-level fields. Fully offline and deterministic.

Machine-readable counts go to stdout; FAIL:/PASS:/WARN:/INFO: detail goes to stderr.
Exit 0 on success, 1 on any FAIL. Exit 2 on usage/input errors.

Edge cases handled:
  * document wrapped as a JSON-RPC envelope ({"result": {...}}) or bare
  * missing/empty file, non-JSON input, non-object payload
  * supportedVersions that is not a list, contains duplicates, or is empty
  * serverInfo that is not an object, or has extra keys (INFO only)
  * strict mode (--strict) turns INFO/WARN into FAIL
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ALLOWED_VERSIONS = ("2026-07-28", "2025-11-25", "2025-06-18")
REQUIRED_RESULT_KEYS = ("supportedVersions", "capabilities", "serverInfo")
REQUIRED_SERVER_INFO_KEYS = ("name", "version")


def load(path: str | None) -> dict:
    if path:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"input file does not exist: {path}")
        if p.is_dir():
            raise IsADirectoryError(f"input path is a directory: {path}")
        raw = p.read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    if not raw.strip():
        raise ValueError("input is empty")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"input is not valid JSON: {exc}") from exc


def check(doc: dict, strict: bool = False) -> tuple[int, int, int]:
    """Return (fails, warns, oks)."""
    fails = warns = oks = 0

    def fail(msg: str) -> None:
        nonlocal fails
        print(f"FAIL: {msg}", file=sys.stderr)
        fails += 1

    def warn(msg: str) -> None:
        nonlocal warns
        if strict:
            fail(msg)
        else:
            print(f"WARN: {msg}", file=sys.stderr)
            warns += 1

    def info(msg: str) -> None:
        if strict:
            fail(msg)
        else:
            print(f"INFO: {msg}", file=sys.stderr)

    if not isinstance(doc, dict):
        fail(f"top-level JSON must be an object, got {type(doc).__name__}")
        return fails, warns, oks

    # Unwrap a JSON-RPC envelope: {"result": {...}} or {"error": ...}
    if "result" in doc and isinstance(doc["result"], dict):
        result = doc["result"]
    elif "error" in doc:
        fail("document is a JSON-RPC error, not a discover result")
        return fails, warns, oks
    else:
        result = doc

    if not isinstance(result, dict):
        fail(f"result must be an object, got {type(result).__name__}")
        return fails, warns, oks

    missing = [k for k in REQUIRED_RESULT_KEYS if k not in result]
    if missing:
        fail(f"server/discover result missing keys: {missing}")
    else:
        oks += 1

    versions = result.get("supportedVersions")
    if not isinstance(versions, list) or not versions:
        fail("supportedVersions must be a non-empty list")
    else:
        if len(versions) != len(set(versions)):
            warn("supportedVersions contains duplicates")
        unknown = [v for v in versions if v not in ALLOWED_VERSIONS]
        if unknown:
            warn(f"supportedVersions contains unknown revisions: {unknown}")
        if "2026-07-28" not in versions:
            info("server does not advertise 2026-07-28")
        oks += 1

    # tasks/result was removed in 2026-07-28 (tasks moved to the extension).
    caps = result.get("capabilities")
    if isinstance(caps, dict):
        tasks = caps.get("tasks")
        if isinstance(tasks, dict):
            methods = tasks.get("methods") or tasks.get("availableMethods")
            if isinstance(methods, list) and "tasks/result" in methods:
                fail("capabilities advertises tasks/result, which was removed in 2026-07-28; use tasks/get from the io.modelcontextprotocol/tasks extension")
            elif isinstance(methods, list) and "tasks/list" in methods:
                warn("capabilities advertises tasks/list, which was removed in 2026-07-28")
        elif tasks is not None:
            info(f"capabilities.tasks is not an object: {type(tasks).__name__}")

    info_obj = result.get("serverInfo")
    if not isinstance(info_obj, dict):
        fail("serverInfo must be an object with name and version")
    else:
        lack = [k for k in REQUIRED_SERVER_INFO_KEYS if k not in info_obj]
        if lack:
            fail(f"serverInfo missing keys: {lack}")
        else:
            oks += 1
        extra = set(info_obj) - set(REQUIRED_SERVER_INFO_KEYS)
        if extra:
            info(f"serverInfo has extra keys: {sorted(extra)}")

    return fails, warns, oks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", nargs="?", help="JSON file (default: stdin)")
    ap.add_argument("--strict", action="store_true",
                    help="treat INFO/WARN as FAIL")
    ap.add_argument("--json", action="store_true",
                    help="emit a machine-readable report object to stdout")
    args = ap.parse_args()

    try:
        doc = load(args.file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: could not read input: {exc}", file=sys.stderr)
        return 2

    fails, warns, oks = check(doc, strict=args.strict)
    if args.json:
        print(json.dumps({"oks": oks, "fails": fails, "warns": warns,
                          "valid": fails == 0}))
        return 1 if fails else 0
    print(f"{oks} {fails} {warns}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
