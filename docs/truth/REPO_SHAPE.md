# REPO_SHAPE — canonical repository shape (source of truth for the canonical-skills job)

Written by SKL-W0-01 TASK-0004 (2026-10-20), re-verified in the VERIFY pass of the
same task (2026-10-20). Every number below is produced by the command in the same
row — re-run them and the document is either true or wrong, never merely plausible.

`tests/hygiene/test_repo_shape_numbers.py` executes every command in the tables of
this document and fails when the printed number differs from the claimed one. The
document cannot drift away from the tree again without turning the suite red.

## One tree, no duplicates

- Every skill lives under **exactly one** directory: `skills/<package>/<skill-name>/`.
- There is **no** top-level `business-de/` and no other duplicate of any skill tree.
- Proof (tracked tree): `git ls-files '*/SKILL.md' | xargs -n1 dirname | xargs -n1 basename | sort | uniq -d`
  → **empty**.
- Proof (worktree): `find . -name SKILL.md | xargs -n1 dirname | xargs -n1 basename | sort | uniq -d`
  → **empty**. The worktree proof only holds while no scratch copy of the tree lives
  inside the repository; `.truth/` is git-ignored working data and must not hold one.

| What | Value | Command |
| --- | --- | --- |
| Skills in the catalogue | 39 | `python3 -c "import json;print(len(json.load(open('catalog.json'))['skills']))"` |
| Packages that contain skills | 12 | `python3 -c "import json;print(len(json.load(open('catalog.json'))['packages']))"` |
| `SKILL.md` files in the tree | 40 | `git ls-files '*/SKILL.md' \| wc -l` |
| Directories under `skills/` | 14 | `ls -d skills/*/ \| wc -l` |
| Tracked files | 652 | `git ls-files \| wc -l` |
| Skill directories with a duplicated name | 0 | `git ls-files '*/SKILL.md' \| xargs -n1 dirname \| xargs -n1 basename \| sort \| uniq -d \| wc -l` |

The 40th `SKILL.md` is `templates/skill/SKILL.md`, the starting point for a new
skill — it is a template, not a skill, so the catalogue holds 39.

Catalogue packages: agentic-data, business-de, core, curated, engineering, orchestrator-preamble, ref-bank-reconciliation-camt, ref-datev-extf, ref-gobd-archive, ref-ust-edge-cases, ref-webhooks-safe, ref-xrechnung-zugferd.

## Flat directory per skill

Each skill is a single self-contained directory:

```
skills/<package>/<skill-name>/
├── SKILL.md                # required — YAML frontmatter + body
├── references/             # DESIGN.md, procedures.md, SOURCES.md, EVALS.md, …
├── scripts/                # implementation scripts
├── tests/                  # test_*.py / *_test.py
└── config/                 # skill-specific config (e.g. versions.json)
```

## Tests outside skill folders

- Repository-level tests live under `tests/`.
- Per-skill tests live under `skills/<package>/<skill-name>/tests/`.
- No test file is collected twice.

| What | Value | Command |
| --- | --- | --- |
| Tracked files under `tests/` | 33 | `git ls-files 'tests/**' \| wc -l` |
| Tracked files under the per-skill `tests/` directories | 112 | `git ls-files 'skills/*/*/tests/**' \| wc -l` |

## Catalogue generated from folders

- `catalog.json` (root) is **generated**, never hand-edited: `scripts/gen-catalog.mjs`
  walks `skills/<package>/<skill-name>/SKILL.md`, parses the YAML frontmatter and writes
  one entry per skill (id, name, title, version, package, path, category, license,
  author, compatibility, description, paths).
- Packages are derived from the `skills/` folders at generation time.
- `index/INDEX.md` and `index/skills.json` are built by `scripts/build-index.py`.
- CI runs `node scripts/gen-catalog.mjs --check`, so the committed catalogue cannot drift.

## Tools — exactly one each

The task requires exactly one `scripts/validate.py` and exactly one
`scripts/install.sh`. Both exist, once each:

| What | Value | Command |
| --- | --- | --- |
| `scripts/install.sh` in the tree | 1 | `git ls-files 'scripts/install.sh' \| wc -l` |
| `scripts/validate.py` in the tree | 1 | `git ls-files 'scripts/validate.py' \| wc -l` |

The complete tool inventory of `scripts/` — one line per tool, no tool twice:

| Tool | Path | Purpose |
| --- | --- | --- |
| Installer | `scripts/install.sh` | copy or link selected skills into an agent skills directory (`--check`, `--dry-run`, `--package`, `--link`, `--force`) |
| Installer (catalogue-driven, overlapping) | `scripts/install-skill.py` | resolves a skill by name or id in `catalog.json` and copies it into an agent directory — a second way to do what `install.sh` does |
| Validator (aggregate) | `scripts/validate.py` | repository structure and catalogue consistency |
| Per-skill validator | `scripts/validate_skill.py` | one or more skill folders against the agentskills.io standard |
| Multi-skill validator | `scripts/validate_skills.py` | the same standard, offline and deterministic, for every skill folder |
| Sign-off validator | `scripts/validate_reviewed_by.py` | enforces the adviser sign-off gate (`reviewed_by:`) |
| Catalogue generator | `scripts/gen-catalog.mjs` | writes `catalog.json` from the `skills/` folders |
| Index builder | `scripts/build-index.py` | writes `index/INDEX.md` and `index/skills.json` |
| Graph checker | `scripts/check_related_graph.py` | proves the Related-section graph of the engineering playbooks is acyclic |
| Lister | `scripts/list-skills.py` | lists skills from the catalogue |
| Preamble generator | `scripts/gen-preamble.mjs` | writes `skills/orchestrator-preamble/references/preamble.md` |
| Honest-status checker | `scripts/verify-status.mjs` | checks a status report against the honest-status table format |

The overlap between `install.sh` and `install-skill.py` is recorded in
`docs/gaps/SKL-W0-01.md` (G21).

## Status / handoff docs: none

| What | Value | Command |
| --- | --- | --- |
| Tracked status diaries anywhere in the tree | 0 | `git ls-files \| grep -E '(^\|/)(STATUS[^/]*\.md\|HANDOFF[^/]*\.md\|GAPS[^/]*\.md\|R3_PLAN\.md\|REVERIFY[^/]*\.md)$' \| wc -l` |

- A status diary is `STATUS*.md`, `HANDOFF*.md`, `GAPS*.md`, `R3_PLAN.md` or
  `REVERIFY*.md`. None of them is committed, at the root or anywhere else.
- The only remaining `EVALS.md` files are **skill content**, not diaries: 30 of the 39
  catalogue skills ship `references/EVALS.md` with their eval prompts, and
  `scripts/validate_skills.py` exits 1 when an engineering skill lacks one. They stay.
- The nine skills without an eval set — `core/work-untill-i-die`, `curated/cursor-cli`,
  `orchestrator-preamble` and the six `ref-*` wrappers — have none by design.
  `scripts/validate_skills.py` only scans `skills/engineering`, so it never asks them for
  one; see `docs/gaps/SKL-W0-01.md` (G24).
- A skill's `references/handoff.md` is likewise skill content (the hand-off contract
  of `browser-agent-playwright`, linked from its `SKILL.md`).
- No `*.log` and no `*.db` is committed. Three `*_state.json` files survive under
  `skills/business-de/` (`immutability-state.json`, `period_lock_state.json`,
  `skr-journal-mapping/period_lock_state.json`); they belong to the business-de lane
  and are not root state files — see `docs/gaps/SKL-W0-01.md` (G4).

## Root contents (authoritative)

```
.github/         # CI workflows
.gitignore
AGENTS.md        # live directives + ownership
CONTRIBUTING.md
LICENSE
README.md
catalog.json     # generated catalogue
docs/            # R3_OWNERS.json, gaps/, truth/, interfaces/, reviews/
index/           # generated INDEX.md, skills.json
schema/          # catalog.schema.json
scripts/         # install.sh, validate.py, gen-catalog.mjs, build-index.py, …
skills/          # the skills
templates/       # SKILL.md template for new skills
tests/           # repository-level test suites
```

Root `*.md` files: AGENTS.md CONTRIBUTING.md README.md
No stray `.md`, `.log`, `.out`, `state.json` or `*.db` beyond that list.

## Follow-up (not deleted here)

Package-level documents that are neither status diaries nor named by the delete list
of this task stay for the canonical-skills job to judge: they are pass records,
research notes and package readmes. The list is generated by one command:

| What | Value | Command |
| --- | --- | --- |
| Package-level documents left for the canonical-skills job | 15 | `git ls-files 'skills/**/*.md' \| grep -vE '/SKILL\.md$' \| grep -vE '^skills/[^/]+/[^/]+/references/' \| grep -vE '^skills/[^/]+/[^/]+/tests/' \| wc -l` |

```
skills/agentic-data/AUDIT.md
skills/agentic-data/README.md
skills/agentic-data/RESEARCH.md
skills/agentic-data/references/PASS2-CONSOLIDATION.md
skills/agentic-data/references/PASS4-R3-02-AUDIT.md
skills/business-de/PASS3_VERIFY.md
skills/business-de/PASS5_GATE.md
skills/business-de/README.md
skills/business-de/RESEARCH.md
skills/community/README.md
skills/engineering/README.md
skills/engineering/RESEARCH.md
skills/engineering/VERIFICATION.md
skills/engineering/references/agentskills-standard.md
skills/ottili-ai/README.md
```

See `docs/gaps/SKL-W0-01.md` (G19).
