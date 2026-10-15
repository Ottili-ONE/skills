# Gaps — SKL-W0-01 (installer, clean clone, catalogue generated from folders)

## cross-job requests

1. **`generic` / `meta` / `ref-*` package names have no definition anywhere.**
   Searched: `catalog.json` (only `core`, `curated`, `community`, `ottili-ai`), all
   `*.md`/`*.json`/`*.yml` in the repo, `git log -p -- catalog.json` (single commit
   `6b81aff Restructure skills repo with catalog, packages, and tooling` — no such
   names ever existed). The task prompt names them as real packages but no other job
   defines them. Resolution adopted inside this job's paths (documented in
   `scripts/install.sh` and `README.md`):
   - `generic` — every skill in the catalogue (all packages).
   - `meta` — reserved name for Ottili's own meta-skills; currently resolves to the
     empty set (no skills have `package: meta`), so `--package meta` installs nothing
     and exits 0 with an explicit message. This is a *virtual* package, not derived
     from a folder, and is intentionally not listed by `gen-catalog.mjs`.
   - `ref-*` — on-demand reference packages. `--package ref-<name>` is accepted and
     resolves to the empty set today; a future job may populate `skills/ref-*`
     folders, at which point `gen-catalog.mjs` will pick them up automatically.
   If another job owns the intended semantics for these names, please define them in
   `catalog.json.packages` and this job will consume them.

2. **`scripts/truth/` (preflight.mjs, gate.mjs, safe-commit.mjs, db.mjs, port.mjs,
   heavy.sh) does not exist in this repository.** The job card and AGENTS.md reference
   it, and the task prompt says to start with
   `node scripts/truth/preflight.mjs --job SKL-W0-01 --status`. A filesystem-wide
   search (`find / -name preflight.mjs`, `find / -type d -name truth -path '*scripts*'`)
   finds no such directory under `/srv/ottili/repo/skills` or anywhere under
   `/srv/ottili/repo`. The `scripts/` directory that exists contains only
   `build-index.py`, `check_related_graph.py`, `install-skill.py`, `install.sh`,
   `list-skills.py`, `validate.py`, `validate_skill.py`, `validate_skills.py`.
   All commits in this pass therefore use plain `git add <paths> && git commit`,
   which is the only mechanism available. This does not block the functional work:
   `install.sh`, `catalog.json`, `validate.py` and `gen-catalog.mjs` are all in this
   job's owned paths and are committed directly.
