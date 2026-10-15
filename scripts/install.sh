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
SKILLS_DIR="$ROOT/skills"
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
  --package <name>       Install every skill in a package.
  --dry-run              Print actions, write nothing, exit 0.
  --force                Overwrite an existing destination folder.
  --link                 Create a symlink instead of copying.
  -h | --help            Show this help.

Packages are DERIVED from the skills/ folders at install time (never a hand-maintained
list). A package is any top-level folder under skills/ that contains skill subfolders.
Virtual packages: 'generic' installs every skill; 'meta' and 'ref-*' are reserved and
currently resolve to the empty set.
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

# --- Derive the package list from the skills/ folders at install time. ---
# A package is a top-level folder under skills/ that contains at least one
# subfolder with a SKILL.md. No hand-maintained list, no dependency on catalog.json.
derive_packages() {
  local pkg
  for pkg in "$SKILLS_DIR"/*/; do
    pkg="$(basename "$pkg")"
    [[ -d "$SKILLS_DIR/$pkg" ]] || continue
    case "$pkg" in
      .git|node_modules|.pytest_cache) continue ;;
    esac
    local sub
    for sub in "$SKILLS_DIR/$pkg"/*/; do
      if [[ -f "$SKILLS_DIR/$pkg/$(basename "$sub")/SKILL.md" ]]; then
        echo "$pkg"
        break
      fi
    done
  done
}

# Expand --package into individual skill names.
if [[ -n "$PACKAGE" ]]; then
  case "$PACKAGE" in
    generic)
      # Every skill in every package.
      while IFS= read -r pkg; do
        for sub in "$SKILLS_DIR/$pkg"/*/; do
          [[ -f "$sub/SKILL.md" ]] || continue
          SKILLS+=("$(basename "$sub")")
        done
      done < <(derive_packages)
      ;;
    meta|ref-*)
      # Reserved virtual package: no skills shipped today.
      echo "note: package '$PACKAGE' resolves to no skills (reserved / on-demand)"
      ;;
    *)
      # Real package: must be a folder under skills/ that contains skills.
      if ! grep -qx "$PACKAGE" <(derive_packages); then
        echo "error: unknown package '$PACKAGE'" >&2
        echo "known packages: $(derive_packages | tr '\n' ' ')" >&2
        exit 1
      fi
      for sub in "$SKILLS_DIR/$PACKAGE"/*/; do
        [[ -f "$sub/SKILL.md" ]] || continue
        SKILLS+=("$(basename "$sub")")
      done
      if [[ ${#SKILLS[@]} -eq 0 ]]; then
        echo "error: no skills in package '$PACKAGE'" >&2
        exit 1
      fi
      ;;
  esac
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
  # Source resolution: a skill folder is skills/<package>/<name>. The package is NOT
  # part of the name the caller passes, so resolve it by searching the skills tree
  # rooted at the script's own directory. This is the ONLY place the source path is
  # computed — the old code did src="$ROOT/$src_dir" where $src_dir came from a
  # python3 -c print() that always appended a newline, so every path carried a
  # trailing newline and the directory check failed for every skill; when the
  # catalog lookup returned nothing the path was also doubled onto $ROOT.
  src=""
  for pkg in "$SKILLS_DIR"/*/; do
    pkg="$(basename "$pkg")"
    [[ -d "$SKILLS_DIR/$pkg/$name" ]] || continue
    src="$SKILLS_DIR/$pkg/$name"
    break
  done
  if [[ -z "$src" ]]; then
    echo "error: source skill directory missing: $SKILLS_DIR/*/$name" >&2
    rc=1; continue
  fi
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
