#!/usr/bin/env bash
# install.sh - copy or link selected Ottili ONE skills into an agent skills directory.
#
# Usage:
#   ./scripts/install.sh --target codex --dry-run pg-rls-multitenant
#   ./scripts/install.sh --target codex pg-rls-multitenant
#   ./scripts/install.sh --target claude --force honest-status
#   ./scripts/install.sh --target cursor --package engineering
#   ./scripts/install.sh --target /tmp/agents/skills --link shared-tree-git
#
# Safety: never overwrites without --force. --dry-run prints what would happen and exits 0.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET=""
DRY_RUN=0
FORCE=0
LINK=0
PACKAGE=""
SKILLS=()

usage() {
  cat <<USAGE
Usage: $0 --target <codex|claude|cursor|agents|/path> [options] <skill...>

Options:
  --target <name|path>   Agent skills directory (required).
  --package <name>       Install every skill in a package (from catalog.json).
  --dry-run              Print actions, write nothing, exit 0.
  --force                Overwrite an existing destination folder.
  --link                 Create a symlink instead of copying.
  -h | --help            Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --target=*) TARGET="${1#*=}"; shift ;;
    --package) PACKAGE="$2"; shift 2 ;;
    --package=*) PACKAGE="${1#*=}"; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --force) FORCE=1; shift ;;
    --link) LINK=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; SKILLS+=("$@"); break ;;
    -*) echo "error: unknown option $1" >&2; usage; exit 2 ;;
    *) SKILLS+=("$1"); shift ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "error: --target is required" >&2
  usage
  exit 2
fi
if [[ ${#SKILLS[@]} -eq 0 && -z "$PACKAGE" ]]; then
  echo "error: at least one skill name or --package is required" >&2
  usage
  exit 2
fi

# Resolve target directory. Named agents map to $HOME subdirs; anything else is a path.
case "$TARGET" in
  codex)   TARGET="$HOME/.codex/skills" ;;
  claude)  TARGET="$HOME/.claude/skills" ;;
  cursor)  TARGET="$HOME/.cursor/skills" ;;
  agents)  TARGET="$HOME/.agents/skills" ;;
esac
mkdir -p "$TARGET"

CATALOG="$ROOT/catalog.json"
if [[ ! -f "$CATALOG" ]]; then
  echo "error: catalog.json not found at $CATALOG" >&2
  exit 1
fi

# Expand --package into individual skill names using python (json is available).
if [[ -n "$PACKAGE" ]]; then
  mapfile -t PKG_SKILLS < <(python3 -c "
import json, sys
cat = json.load(open('$CATALOG'))
pkgs = cat.get('packages', {})
if '$PACKAGE' not in pkgs:
    print('error: unknown package $PACKAGE', file=sys.stderr); sys.exit(1)
for s in cat.get('skills', []):
    if s.get('package') == '$PACKAGE':
        print(s['name'])
")
  if [[ ${#PKG_SKILLS[@]} -eq 0 ]]; then
    echo "error: no skills in package '$PACKAGE'" >&2
    exit 1
  fi
  SKILLS+=("${PKG_SKILLS[@]}")
fi

# Deduplicate while preserving order.
declare -A SEEN=()
UNIQ=()
for s in "${SKILLS[@]}"; do
  if [[ -z "${SEEN[$s]:-}" ]]; then
    SEEN[$s]=1; UNIQ+=("$s")
  fi
done
SKILLS=("${UNIQ[@]}")

rc=0
for name in "${SKILLS[@]}"; do
  src_dir="$ROOT/skills/$(python3 -c "
import json
cat = json.load(open('$CATALOG'))
for s in cat.get('skills', []):
    if s['name'] == '$name' or s['id'] == '$name':
        print(s['path']); break
else:
    print('')
")
"
  if [[ -z "$src_dir" ]]; then
    echo "error: skill '$name' not found in catalog" >&2
    rc=1; continue
  fi
  src="$ROOT/$src_dir"
  dest="$TARGET/$name"

  if [[ ! -d "$src" ]]; then
    echo "error: source skill directory missing: $src" >&2
    rc=1; continue
  fi
  if [[ ! -f "$src/SKILL.md" ]]; then
    echo "error: $src has no SKILL.md" >&2
    rc=1; continue
  fi

  if [[ -e "$dest" || -L "$dest" ]]; then
    if [[ $FORCE -eq 0 ]]; then
      echo "skip: $dest already exists (use --force to overwrite)"
      continue
    fi
    rm -rf "$dest"
  fi

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "dry-run: $LINK=1 ? link : copy  $src  ->  $dest"
    continue
  fi

  if [[ $LINK -eq 1 ]]; then
    ln -s "$src" "$dest"
    echo "linked:  $dest -> $src"
  else
    cp -r "$src" "$dest"
    echo "copied: $dest"
  fi
done

exit $rc
