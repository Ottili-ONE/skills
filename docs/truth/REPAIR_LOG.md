# REPAIR_LOG — SKL-W0-01 (installer path bug and package catalogue)

## D-001 — install.sh source resolution doubled the path for every skill

- **Defect:** `./scripts/install.sh --target claude honest-status` exited with
  `error: source skill directory missing: /srv/ottili/repo/skills//srv/ottili/repo/skills/skills/\n`
  (note the doubled path and the trailing newline).
- **Cause (two bugs in one line):**
  1. The source path was resolved through `catalog.json` via
     `python3 -c "...print(s['path'])"`. The skill was **not** in the catalogue
     (the catalogue listed only 2 of 32 skills), so `print('')` returned an empty
     string — but `print` always appends a newline, so `src_dir` was `"\n"`.
  2. The directory was then built as `src="$ROOT/$src_dir"`, which concatenated
     `$ROOT` onto the empty-but-newline-terminated string, producing
     `$ROOT//<repo>/skills/\n`. The `-z` test passed because the string was not
     zero-length, and the `-d` test failed for every skill.
- **Fix:** removed the catalogue lookup entirely. The source path is now resolved
  by searching the `skills/` tree rooted at the script's own directory for a
  folder named after the skill:
  `src="" ; for pkg in "$SKILLS_DIR"/*/; do ...; src="$SKILLS_DIR/$pkg/$name"; break; done`.
  The folder name IS the skill name; no catalogue, no relative-to-script mistake.
- **Proof:** `bash -x` before (doubled path, `-d` failed) and after (32/32 folders
  resolve). See `.truth/SKL-W0-01/before.txt` and `.truth/SKL-W0-01/after.txt`.

## D-002 — `--package engineering|business-de|agentic-data` reported "unknown package"

- **Defect:** every named package printed `error: unknown package <name>`.
- **Cause:** the package list was read from `catalog.json`'s `packages` object,
  which contained only `core`, `curated`, `community`, `ottili-ai` (a
  hand-maintained, stale list).
- **Fix:** packages are now **DERIVED from the `skills/` folders at install time**.
  `derive_packages()` walks `skills/*/`, skips `.git`/`node_modules`/`.pytest_cache`,
  and emits a package name for every top-level folder that contains at least one
  subfolder with a `SKILL.md`. `--package <name>` validates against that derived
  list. Virtual packages `generic` (every skill), `meta` and `ref-*` (reserved,
  empty set) are handled explicitly.
- **Proof:** `--package engineering` installs 10/10, `business-de` 11/11,
  `agentic-data` 10/10, `generic` 32/32; `--package bogus` exits 1 with the known
  list. See `.truth/SKL-W0-01/after.txt`.

## D-003 — catalogue listed only 2 of 32 skills and was hand-edited

- **Defect:** `python3 -I scripts/validate.py` printed `ok: 2 skills validated`.
- **Cause:** `catalog.json` was a hand-written file with 2 entries and a stale
  `packages` object; nothing regenerated it.
- **Fix:** added `scripts/gen-catalog.mjs`, which walks `skills/<package>/<name>/SKILL.md`,
  parses the YAML frontmatter (block-style lists, quoted scalars) and writes one
  entry per skill with `name`, `package`, `description` and `paths`. Packages are
  derived from the folders. Cache/build artefacts (`.pytest_cache`, `__pycache__`,
  `node_modules`, `.git`, `.DS_Store`) are excluded and `paths` are sorted, so the
  output is deterministic. `--check` fails if the committed file would change.
  CI (`.github/workflows/validate.yml`) runs `node scripts/gen-catalog.mjs --check`.
- **Proof:** `node scripts/gen-catalog.mjs` writes 32 skills / 5 packages;
  `--check` exits 0; `validate.py` prints `ok: 32 skills validated`.

## Verification commands run

```
node scripts/gen-catalog.mjs            # 32 skills, 5 packages
node scripts/gen-catalog.mjs --check    # exit 0, unchanged
python3 -I scripts/validate.py          # ok: 32 skills validated
python3 scripts/validate_skill.py --all # 10/10 engineering skills
python3 scripts/build-index.py          # index regenerated
./scripts/install.sh --target <dir> --package engineering   # 10 skills
./scripts/install.sh --target <dir> --package business-de   # 11 skills
./scripts/install.sh --target <dir> --package agentic-data  # 10 skills
./scripts/install.sh --target <dir> --package generic       # 32 skills
./scripts/install.sh --target <dir> --link honest-status    # symlink
./scripts/install.sh --target <dir> --dry-run honest-status # no write
```
All engineering self-tests (`*_test.py`, `tests/*.py`, `run_long_test_test.sh`) pass.
