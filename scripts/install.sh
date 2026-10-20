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
#   ./scripts/install.sh --check
#   ./scripts/install.sh --target "$(mktemp -d)" --package engineering --json
#
# Safety: never overwrites without --force. --dry-run prints what would happen and
# exits 0. --check verifies every source and the target without writing anything.
#
# Contract: with --json the script prints ONE JSON object and nothing else, the
# install manifest of contract ottili.skills.install-manifest/v1. Its JSON Schema
# is scripts/ottili_contracts/schemas/ottili.skills.install-manifest.v1.schema.json,
# its typed view scripts/ottili_contracts/models.py and its example
# scripts/ottili_contracts/examples/. In --json mode stdout carries the manifest
# and stderr stays empty; every message of the human mode is carried by the
# manifest ("error" for the run, "error" per skill).
#
# Exit codes: 0 success, 1 a skill or a package could not be resolved,
# 2 usage error (missing --target, missing selection, unknown option).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT/skills"
MANIFEST_LIB="$ROOT/scripts/lib/install-manifest.sh"
TARGET=""
TARGET_GIVEN=0
DRY_RUN=0
FORCE=0
LINK=0
CHECK=0
CHECK_ALL=0
PACKAGE=""
JSON=0
SKILLS=()

# The manifest rows of the current run: name|package|source|destination|action|error
MANIFEST_ROWS=()
MANIFEST_MODE="install"

if [[ ! -f "$MANIFEST_LIB" ]]; then
  echo "error: $MANIFEST_LIB is missing; the installer needs the repository layout" >&2
  exit 2
fi
# shellcheck source=scripts/lib/install-manifest.sh
source "$MANIFEST_LIB"

# Print the usage text of the installer.
#
# Inputs: none.
# Outputs: the usage text on stdout.
# Failure modes: none.
usage() {
  cat <<USAGE
Usage: $0 --target <codex|claude|cursor|agents|/path> [options] <skill...>

Options:
  --target <name|path>   Agent skills directory (required, except in --check
                         mode where a scratch directory is used).
  --package <name>       Install every skill in a package.
  --check                Verify without writing: every skill must resolve to a
                         folder with a SKILL.md and the target must be writable.
                         Without --target and without a skill selection the whole
                         repository is verified against a scratch directory that
                         is never created.
  --dry-run              Print actions, write nothing, exit 0.
  --force                Overwrite an existing destination folder.
  --link                 Create a symlink instead of copying.
  --json                 Print the install manifest (contract
                         ottili.skills.install-manifest/v1) as one JSON object on
                         stdout and nothing else.
  --version              Print the contract id of the manifest and exit 0.
  -h | --help            Show this help.

Exit codes:
  0  every requested skill was installed, linked, skipped or verified
  1  a skill or a package could not be resolved
  2  usage error (missing --target, missing skill/package, unknown option)

Packages are DERIVED from the skills/ folders at install time (never a hand-maintained
list). A package is any top-level folder under skills/ that contains skill subfolders.
Virtual package: 'generic' installs every skill of every package. 'meta' is reserved
and ships no skills unless a skills/meta/ folder exists.
USAGE
}

# Print one message of the human mode and, in --json mode, the manifest of a
# run that could not start.
#
# Inputs: the exit code and the message.
# Outputs: the message on stderr (human mode) or the manifest on stdout
#   (--json mode).
# Failure modes: none, the function exits with the given code.
usage_error() {
  local code="$1"; shift
  if [[ $JSON -eq 1 ]]; then
    manifest_emit "$*"
  else
    echo "error: $*" >&2
    usage
  fi
  exit "$code"
}

# Report one skill that could not be resolved.
#
# Inputs: the message and the name of the skill.
# Outputs: the message on stderr (human mode); the row is recorded in the
#   manifest in every mode.
# Failure modes: none.
report_error() {
  local message="$1" name="$2"
  manifest_add "$name" "" "" "" "error" "$message"
  [[ $JSON -eq 1 ]] || echo "error: $message" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; TARGET_GIVEN=1; shift 2 ;;
    --target=*) TARGET="${1#*=}"; TARGET_GIVEN=1; shift ;;
    --package) PACKAGE="$2"; shift 2 ;;
    --package=*) PACKAGE="${1#*=}"; shift ;;
    --check) CHECK=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --force) FORCE=1; shift ;;
    --link) LINK=1; shift ;;
    --json) JSON=1; shift ;;
    --version) echo "install.sh - contract ottili.skills.install-manifest/v1"; exit 0 ;;
    -h|--help) usage; exit 0 ;;
    --) shift; SKILLS+=("$@"); break ;;
    -*) usage_error 2 "unknown option $1" ;;
    *) SKILLS+=("$1"); shift ;;
  esac
done

# A skill name is a plain folder name. The name becomes a path component of
# the destination ("$TARGET/$name"), so a name that carries a path separator
# ("../pkg/skill") would let the installer write — and with --force DELETE —
# outside the target directory. Such a name is refused before anything is
# written; every skill folder of this tree matches the accepted charset.
#
# Inputs: the candidate name.
# Outputs: 0 when the name is a plain folder name, 1 otherwise.
# Failure modes: none, the function never writes and never exits.
valid_skill_name() {
  local name="$1"
  [[ -n "$name" ]] || return 1
  [[ "$name" != */* ]] || return 1
  [[ "$name" != "." && "$name" != ".." ]] || return 1
  [[ "$name" != -* ]] || return 1
  [[ "$name" =~ ^[A-Za-z0-9._-]+$ ]] || return 1
  return 0
}

if [[ ${#SKILLS[@]} -gt 0 ]]; then
  for name in "${SKILLS[@]}"; do
    if ! valid_skill_name "$name"; then
      usage_error 2 "invalid skill name '$name': a skill name must be a plain folder name (letters, digits, '.', '_' and '-')"
    fi
  done
fi

# `--check` without a --target verifies the whole repository. The gate runs
# exactly `bash scripts/install.sh --check`, so the check has to be meaningful
# on its own: it resolves every skill of every package and checks the scratch
# target it would use, and it writes nothing at all.
if [[ $CHECK -eq 1 && $TARGET_GIVEN -eq 0 ]]; then
  scratch_root="${TMPDIR:-/tmp}"
  [[ -d "$scratch_root" ]] || scratch_root="/tmp"
  TARGET="$scratch_root/ottili-install-check"
  if [[ ${#SKILLS[@]} -eq 0 && -z "$PACKAGE" ]]; then
    CHECK_ALL=1
  fi
fi

if [[ -z "$TARGET" ]]; then
  usage_error 2 "--target is required"
fi
if [[ ${#SKILLS[@]} -eq 0 && -z "$PACKAGE" && $CHECK_ALL -eq 0 ]]; then
  usage_error 2 "at least one skill name or --package is required"
fi

# Resolve target directory. Named agents map to $HOME subdirs; anything else is a path.
case "$TARGET" in
  codex)   TARGET="$HOME/.codex/skills" ;;
  claude)  TARGET="$HOME/.claude/skills" ;;
  cursor)  TARGET="$HOME/.cursor/skills" ;;
  agents)  TARGET="$HOME/.agents/skills" ;;
esac

if [[ $CHECK -eq 1 ]]; then
  MANIFEST_MODE="check"
elif [[ $DRY_RUN -eq 1 ]]; then
  MANIFEST_MODE="dry-run"
else
  MANIFEST_MODE="install"
fi

# --- Derive the package list from the skills/ folders at install time. ---
# A package is a top-level folder under skills/ that contains at least one
# subfolder with a SKILL.md. No hand-maintained list, no dependency on catalog.json.
#
# Inputs: none.
# Outputs: the package names, one per line, on stdout.
# Failure modes: none, an unreadable skills/ tree yields no package.
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
#
# Inputs: the package name.
# Outputs: the skill names of that package, one per line, on stdout.
# Failure modes: none, an unknown package yields no name.
skills_in_package() {
  local pkg="$1" sub
  for sub in "$SKILLS_DIR/$pkg"/*/; do
    [[ -f "$sub/SKILL.md" ]] || continue
    basename "$sub"
  done
}

# Print every package that contains a folder named $1, one per line.
#
# Inputs: the skill name.
# Outputs: the names of the packages that hold that skill, one per line.
# Failure modes: none, an unknown skill yields no package.
packages_holding() {
  local name="$1" pkg
  for pkg in "$SKILLS_DIR"/*/; do
    [[ -d "$pkg/$name" ]] || continue
    basename "$pkg"
  done
}

# Auxiliary folders inside a package are not skills: they carry the references,
# scripts, tests and configuration of the skills next to them. Every other
# folder of a package is a skill folder and therefore has to hold a SKILL.md.
AUX_FOLDERS=" references scripts tests config "

# Print every package folder of the tree, derived ones or not.
#
# Inputs: none.
# Outputs: the package folder names, one per line, on stdout.
# Failure modes: none.
all_packages() {
  local pkg
  for pkg in "$SKILLS_DIR"/*/; do
    [[ -d "$pkg" ]] || continue
    case "$(basename "$pkg")" in
      .git|node_modules|.pytest_cache|__pycache__) continue ;;
    esac
    basename "$pkg"
  done
}

# Print every skill folder of one package, even one without a SKILL.md: such a
# folder is exactly what --check has to report.
#
# Inputs: the package name.
# Outputs: the folder names of that package, one per line, on stdout.
# Failure modes: none.
skill_folders_in_package() {
  local pkg="$1" sub name
  for sub in "$SKILLS_DIR/$pkg"/*/; do
    [[ -d "$sub" ]] || continue
    name="$(basename "$sub")"
    case "$AUX_FOLDERS" in
      *" $name "*) continue ;;
    esac
    echo "$name"
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
    [[ $JSON -eq 1 ]] || echo "note: package 'meta' is reserved and ships no skills in this tree"
  else
    usage_error 1 "unknown package '$PACKAGE'; known packages: $(derive_packages | tr '\n' ' ') generic meta"
  fi
fi

# --check without a skill selection verifies every skill folder of every package.
if [[ $CHECK_ALL -eq 1 ]]; then
  while IFS= read -r pkg; do
    while IFS= read -r name; do
      SKILLS+=("$name")
    done < <(skill_folders_in_package "$pkg")
  done < <(all_packages)
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
  RUN_ERROR=""
  if [[ -e "$TARGET" ]]; then
    if [[ ! -d "$TARGET" ]]; then
      RUN_ERROR="target '$TARGET' exists and is not a directory"
      rc=1
    elif [[ ! -w "$TARGET" ]]; then
      RUN_ERROR="target '$TARGET' is not writable"
      rc=1
    fi
  else
    # The install creates the target tree with `mkdir -p`, so a missing parent
    # directory is NOT an error: the check has to look at the nearest
    # EXISTING ancestor and ask whether the tree could be created there. A
    # check that is stricter than the install reports a false failure for a
    # target the install would accept.
    ancestor="$TARGET"
    while [[ ! -e "$ancestor" ]]; do
      ancestor_parent="$(dirname "$ancestor")"
      [[ "$ancestor_parent" == "$ancestor" ]] && break
      ancestor="$ancestor_parent"
    done
    if [[ ! -d "$ancestor" ]]; then
      RUN_ERROR="target '$TARGET' cannot be created: '$ancestor' is not a directory"
      rc=1
    elif [[ ! -w "$ancestor" ]]; then
      RUN_ERROR="target parent '$ancestor' is not writable"
      rc=1
    fi
  fi
  [[ $JSON -eq 1 ]] || [[ -z "$RUN_ERROR" ]] || echo "error: $RUN_ERROR" >&2

  for name in "${SKILLS[@]}"; do
    mapfile -t holders < <(packages_holding "$name")
    if [[ ${#holders[@]} -eq 0 ]]; then
      report_error "source skill directory missing: $SKILLS_DIR/*/$name" "$name"
      rc=1
      continue
    fi
    if [[ ${#holders[@]} -gt 1 ]]; then
      report_error "skill '$name' is ambiguous, found in packages: ${holders[*]}" "$name"
      rc=1
      continue
    fi
    src="$SKILLS_DIR/${holders[0]}/$name"
    if [[ ! -f "$src/SKILL.md" ]]; then
      report_error "$src has no SKILL.md" "$name"
      rc=1
      continue
    fi
    dest="$TARGET/$name"
    if [[ -e "$dest" || -L "$dest" ]]; then
      if [[ $FORCE -eq 0 ]]; then
        manifest_add "$name" "${holders[0]}" "$src" "$dest" "would-skip"
        [[ $JSON -eq 1 ]] || echo "would skip: $dest already exists (use --force to overwrite)"
        continue
      fi
      manifest_add "$name" "${holders[0]}" "$src" "$dest" "would-overwrite"
      [[ $JSON -eq 1 ]] || echo "would overwrite: $dest"
    else
      manifest_add "$name" "${holders[0]}" "$src" "$dest" "verified"
      [[ $JSON -eq 1 ]] || echo "ok: $name -> $dest"
    fi
  done
  if [[ $JSON -eq 1 ]]; then
    manifest_emit "$RUN_ERROR"
  elif [[ $rc -eq 0 ]]; then
    echo "check: ${#SKILLS[@]} skill(s) verified, nothing written"
  else
    echo "check: FAILED" >&2
  fi
  exit $rc
fi

# --dry-run promises to write nothing at all, so the target directory is only
# created when something is actually going to be written into it.
if [[ $DRY_RUN -eq 0 ]]; then
  if ! mkdir -p "$TARGET" 2>/dev/null; then
    usage_error 1 "target '$TARGET' cannot be created"
  fi
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
    report_error "source skill directory missing: $SKILLS_DIR/*/$name" "$name"
    rc=1; continue
  fi
  if [[ ${#holders[@]} -gt 1 ]]; then
    report_error "skill '$name' is ambiguous, found in packages: ${holders[*]}" "$name"
    rc=1; continue
  fi
  src="$SKILLS_DIR/${holders[0]}/$name"
  dest="$TARGET/$name"

  if [[ ! -d "$src" ]]; then
    report_error "source skill directory missing: $src" "$name"
    rc=1; continue
  fi
  if [[ ! -f "$src/SKILL.md" ]]; then
    report_error "$src has no SKILL.md" "$name"
    rc=1; continue
  fi

  if [[ -e "$dest" || -L "$dest" ]]; then
    if [[ $FORCE -eq 0 ]]; then
      manifest_add "$name" "${holders[0]}" "$src" "$dest" "skipped"
      [[ $JSON -eq 1 ]] || echo "skip: $dest already exists (use --force to overwrite)"
      continue
    fi
    rm -rf "$dest"
  fi

  if [[ $DRY_RUN -eq 1 ]]; then
    if [[ $LINK -eq 1 ]]; then
      manifest_add "$name" "${holders[0]}" "$src" "$dest" "would-link"
      [[ $JSON -eq 1 ]] || echo "dry-run: link  $src  ->  $dest"
    else
      manifest_add "$name" "${holders[0]}" "$src" "$dest" "would-copy"
      [[ $JSON -eq 1 ]] || echo "dry-run: copy  $src  ->  $dest"
    fi
    continue
  fi

  if [[ $LINK -eq 1 ]]; then
    ln -s "$src" "$dest"
    manifest_add "$name" "${holders[0]}" "$src" "$dest" "linked"
    [[ $JSON -eq 1 ]] || echo "linked:  $dest -> $src"
  else
    cp -r "$src" "$dest"
    manifest_add "$name" "${holders[0]}" "$src" "$dest" "copied"
    [[ $JSON -eq 1 ]] || echo "copied: $dest"
  fi
done

if [[ $JSON -eq 1 ]]; then
  manifest_emit
fi
exit $rc
