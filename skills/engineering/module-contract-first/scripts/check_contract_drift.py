#!/usr/bin/env python3
"""Check module contract drift against a committed snapshot.

Offline-deterministic: no network calls, no subprocesses beyond stdlib.
Small (<200 LOC), runs <1s on typical Ottili modules.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import ast
except ImportError:  # pragma: no cover
    ast = None  # type: ignore[assignment]


def _walk_py(root: Path) -> list:
    """Return sorted list of top-level exported symbol names in Python files."""
    symbols = []
    for p in sorted(root.rglob("*.py")):
        try:
            src = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"warning: skipping binary file {p}", file=sys.stderr)
            continue
        if ast is None:
            for line in src.splitlines():
                s = line.strip()
                if s.startswith("def ") or s.startswith("class "):
                    name = s.split("(", 1)[0].split()[-1].split(":", 1)[0]
                    if name and not name.startswith("_"):
                        symbols.append(name)
            continue
        try:
            tree = ast.parse(src, filename=str(p))
        except SyntaxError:
            continue
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    symbols.append(node.name)
    return sorted(set(symbols))
def _snapshot_path(mc_dir: Path, target: Path) -> Path:
    return mc_dir / (target.name + ".json")


def _load_snapshot(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _write_snapshot(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write(chr(10))


def _diff_lines(old: dict, new: dict) -> list:
    lines = []
    for key in sorted(set(old) | set(new)):
        if old.get(key) != new.get(key):
            lines.append(f"@@ {key} @@")
            lines.append(f"- old: {old.get(key)!r}")
            lines.append(f"+ new: {new.get(key)!r}")
    return lines


def cmd_enumerate(args: argparse.Namespace) -> int:
    target = _resolve_target(args)
    surface = {"symbols": _walk_py(target)}
    path = _snapshot_path(_mc_dir(target, args), target)
    _write_snapshot(path, surface)
    print(f"ok: enumerated {len(surface['symbols'])} symbols -> {path}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    target = _resolve_target(args)
    mc_dir = _mc_dir(target, args)
    path = _snapshot_path(mc_dir, target)
    if not path.is_file():
        print(f"error: snapshot missing {path}; run --enumerate first", file=sys.stderr)
        return 1
    live = {"symbols": _walk_py(target)}
    stored = _load_snapshot(path)
    diff = _diff_lines(stored, live)
    if not diff:
        print(f"ok: {target.name} contract matches snapshot ({len(live['symbols'])} symbols)")
        return 0
    print("DRIFT DETECTED", file=sys.stderr)
    print("--- live", file=sys.stderr)
    print("+++ snapshot", file=sys.stderr)
    for line in diff:
        print(line, file=sys.stderr)
    print("BLOCKED: merge until snapshot regenerated or reverted", file=sys.stderr)
    return 1


def cmd_cycles(args: argparse.Namespace) -> int:
    target = _resolve_target(args)
    imports = _build_import_graph(target)
    cycle = _find_cycle(imports)
    if cycle:
        print("CYCLE DETECTED", file=sys.stderr)
        print(" -> ".join(cycle), file=sys.stderr)
        print("Break cycle by extracting shared types into an internal-only module", file=sys.stderr)
        return 1
    print(f"ok: no import cycles in {target.name}")
    return 0


def _resolve_target(args: argparse.Namespace) -> Path:
    raw = args.check or args.enumerate or args.cycles or "."
    target = Path(raw)
    return target if target.is_absolute() else Path.cwd() / target


def _mc_dir(target: Path, args: argparse.Namespace) -> Path:
    if args.snapshot_dir:
        return Path(args.snapshot_dir)
    return target / "module-contracts"


def _build_import_graph(root: Path) -> dict:
    """Map module name -> set of imported module names (offline, stdlib only)."""
    graph: dict = {}
    for p in sorted(root.rglob("*.py")):
        try:
            src = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if ast is None:
            continue
        try:
            tree = ast.parse(src, filename=str(p))
        except SyntaxError:
            continue
        mod = p.stem
        deps = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    deps.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    deps.add(node.module.split(".")[0])
        graph.setdefault(mod, set()).update(deps)
    return graph


def _find_cycle(graph: dict) -> list | None:
    """Return a cycle path if any back-edge exists (DFS)."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}
    stack: list = []

    def dfs(node: str) -> list | None:
        color[node] = GRAY
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            if color.get(nxt, WHITE) == GRAY:
                return stack[stack.index(nxt):] + [nxt]
            if color.get(nxt, WHITE) == WHITE:
                cycle = dfs(nxt)
                if cycle:
                    return cycle
        stack.pop()
        color[node] = BLACK
        return None

    for node in sorted(graph):
        if color[node] == WHITE:
            cycle = dfs(node)
            if cycle:
                return cycle
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Module contract drift checker")
    parser.add_argument("--enumerate", metavar="DIR")
    parser.add_argument("--check", metavar="DIR")
    parser.add_argument("--cycles", metavar="DIR")
    parser.add_argument("--snapshot-dir", default=None)
    args = parser.parse_args()
    if args.enumerate:
        return cmd_enumerate(args)
    if args.check:
        return cmd_check(args)
    if args.cycles:
        return cmd_cycles(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
