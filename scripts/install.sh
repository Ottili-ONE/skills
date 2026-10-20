#!/usr/bin/env bash
# install.sh - copy or link selected Ottili ONE skills into an agent skills directory.
#
# Usage:
#   ./scripts/install.sh --target codex --dry-run pg-rls-multitenant
#   ./scripts/install.sh --target codex pg-rls-multitenant
#   ./scripts/install.sh --target claude --force honest-status
#   ./scripts/install.sh --target cursor --package engineering
#   ./scripts/install.sh --target /tmp/agents/skills --link shared-tree-git
#   ./scripts/install.sh --check --target /tmp/agents/skills --package generic
#
# Safety: never overwrites without --force. --dry-run prints what would happen and
# exits 0. --check verifies every source and the target without writing anything.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT/skills"
TARGET=""
DRY_RUN=0
FORCE=0
LINK=0
CHECK=0
PACKAGE=""
SKILLS=()

usage() {
  cat <<USAGE
Usage: $0 --target <codex|claude|cursor|agents|/path> [options] <skill...>

Options:
  --target <name|path>   Agent skills directory (required).
  --package <name>       Install every skill in a package.
  --check                Verify without writing: every skill must resolve to a
                         folder with a SKILL.md and the target must be writable.
  --dry-run              Print actions, write nothing, exit 0.
  --force                Overwrite an existing destination folder.
  --link                 Create a symlink instead of copying.
  -h | --help            Show this help.

Packages are DERIVED from the skills/ folders at install time (never a hand-maintained
list). A package is any top-level folder under skills/ that contains skill subfolders.
Virtual package: 'generic' installs every skill of every package. 'meta' is reserved
and ships no skills unless a skills/meta/ folder exists.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --target=*) TARGET="${1#*=}"; shift ;;
    --package) PACKAGE="$2"; shift 2 ;;
    --package=*) PACKAGE="${1#*=}"; shift ;;
    --check) CHECK=1; shift ;;
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

# --- Derive the package list from the skills/ folders at install time. ---
# A package is a top-level folder under skills/ that contains at least one
# subfolder with a SKILL.md. No hand-maintained list, no dependency on catalog.json.
derive_packages() {
  local pkg sub
  for pkg in "$SKILLS_DIR"/*/; do
    [[ -d "$pkg" ]] || continue
    pkg="$(basename "$pkg")"
    case "$pkg" in
      .git|node_modules|.pytest_cache|__pycache__) continue ;;
    esac
    for sub in "$SKILLS_DIR/$pkg"/*/; do
      if [[ -f "$sub/SKILL.md" ]]; then
        echo "$pkg"
        break
      fi
    done
  done
}

# Print the skill names of one package, one per line.
skills_in_package() {
  local pkg="$1" sub
  for sub in "$SKILLS_DIR/$pkg"/*/; do
    [[ -f "$sub/SKILL.md" ]] || continue
    basename "$sub"
  done
}

# Print every package that contains a folder named $1, one per line.
packages_holding() {
  local name="$1" pkg
  for pkg in "$SKILLS_DIR"/*/; do
    [[ -d "$pkg/$name" ]] || continue
    basename "$pkg"
  done
}

# Expand --package into individual skill names.
if [[ -n "$PACKAGE" ]]; then
  # -F: the package name is matched literally. Without it a name that happens
  # to be a valid regex ("engineering+") would match a package it does not
  # exist and install the wrong skills.
  if grep -qxF "$PACKAGE" <(derive_packages); then
    # Real package (derived from the folders): install every skill it contains.
    while IFS= read -r name; do
      SKILLS+=("$name")
    done < <(skills_in_package "$PACKAGE")
  elif [[ "$PACKAGE" == "generic" ]]; then
    # Every skill in every package.
    while IFS= read -r pkg; do
      while IFS= read -r name; do
        SKILLS+=("$name")
      done < <(skills_in_package "$pkg")
    done < <(derive_packages)
  elif [[ "$PACKAGE" == "meta" ]]; then
    # Reserved virtual package: no skills/meta/ folder in this tree.
    echo "note: package 'meta' is reserved and ships no skills in this tree"
  else
    echo "error: unknown package '$PACKAGE'" >&2
    echo "known packages: $(derive_packages | tr '\n' ' ') generic meta" >&2
    exit 1
  fi
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

# --- --check: verify the preconditions, write nothing. ---
if [[ $CHECK -eq 1 ]]; then
  rc=0
  target_parent="$(dirname "$TARGET")"
  if [[ -e "$TARGET" ]]; then
    if [[ ! -d "$TARGET" ]]; then
      echo "error: target '$TARGET' exists and is not a directory" >&2
      rc=1
    elif [[ ! -w "$TARGET" ]]; then
      echo "error: target '$TARGET' is not writable" >&2
      rc=1
    fi
  elif [[ ! -d "$target_parent" ]]; then
    echo "error: target parent '$target_parent' does not exist" >&2
    rc=1
  elif [[ ! -w "$target_parent" ]]; then
    echo "error: target parent '$target_parent' is not writable" >&2
    rc=1
  fi

  for name in "${SKILLS[@]}"; do
    mapfile -t holders < <(packages_holding "$name")
    if [[ ${#holders[@]} -eq 0 ]]; then
      echo "error: source skill directory missing: $SKILLS_DIR/*/$name" >&2
      rc=1
      continue
    fi
    if [[ ${#holders[@]} -gt 1 ]]; then
      echo "error: skill '$name' is ambiguous, found in packages: ${holders[*]}" >&2
      rc=1
      continue
    fi
    src="$SKILLS_DIR/${holders[0]}/$name"
    if [[ ! -f "$src/SKILL.md" ]]; then
      echo "error: $src has no SKILL.md" >&2
      rc=1
      continue
    fi
    dest="$TARGET/$name"
    if [[ -e "$dest" || -L "$dest" ]]; then
      if [[ $FORCE -eq 0 ]]; then
        echo "would skip: $dest already exists (use --force to overwrite)"
        continue
      fi
      echo "would overwrite: $dest"
    else
      echo "ok: $name -> $dest"
    fi
  done
  if [[ $rc -eq 0 ]]; then
    echo "check: ${#SKILLS[@]} skill(s) verified, nothing written"
  else
    echo "check: FAILED" >&2
  fi
  exit $rc
fi

# --dry-run promises to write nothing at all, so the target directory is only
# created when something is actually going to be written into it.
if [[ $DRY_RUN -eq 0 ]]; then
  mkdir -p "$TARGET"
fi

rc=0
for name in "${SKILLS[@]}"; do
  # Source resolution: a skill folder is skills/<package>/<name>. The package is NOT
  # part of the name the caller passes, so resolve it by searching the skills tree
  # rooted at the script's own directory. This is the ONLY place the source path is
  # computed — the old code did src="$ROOT/$src_dir" where $src_dir came from a
  # python3 -c print() that always appended a newline, so every path carried a
  # trailing newline and the directory check failed for every skill; when the
  # catalog lookup returned nothing the path was also doubled onto $ROOT.
  mapfile -t holders < <(packages_holding "$name")
  if [[ ${#holders[@]} -eq 0 ]]; then
    echo "error: source skill directory missing: $SKILLS_DIR/*/$name" >&2
    rc=1; continue
  fi
  if [[ ${#holders[@]} -gt 1 ]]; then
    echo "error: skill '$name' is ambiguous, found in packages: ${holders[*]}" >&2
    rc=1; continue
  fi
  src="$SKILLS_DIR/${holders[0]}/$name"
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
    if [[ $LINK -eq 1 ]]; then echo "dry-run: link  $src  ->  $dest"; else echo "dry-run: copy  $src  ->  $dest"; fi
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
