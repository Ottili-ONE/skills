# REPO_SHAPE — canonical repository shape (source of truth for the canonical-skills job)

Written by SKL-W0-01 TASK-0004 (2026-10-20). Every number below is produced by the
command in the same row — re-run them and the document is either true or wrong, never
merely plausible.

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
| Tracked files | 649 | `git ls-files \| wc -l` |

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

- Repository-level tests live under `tests/` (30 tracked files).
- Per-skill tests live under `skills/<package>/<skill-name>/tests/` (112 tracked files).
- No test file is collected twice.

| What | Value | Command |
| --- | --- | --- |
| Repository-level test files | 30 | `git ls-files 'tests/**' \| wc -l` |
| Per-skill test files | 112 | `git ls-files 'skills/*/*/tests/**' \| wc -l` |

## Catalogue generated from folders

- `catalog.json` (root) is **generated**, never hand-edited: `scripts/gen-catalog.mjs`
  walks `skills/<package>/<skill-name>/SKILL.md`, parses the YAML frontmatter and writes
  one entry per skill (id, name, title, version, package, path, category, license,
  author, compatibility, description, paths).
- Packages are derived from the `skills/` folders at generation time.
- `index/INDEX.md` and `index/skills.json` are built by `scripts/build-index.py`.
- CI runs `node scripts/gen-catalog.mjs --check`, so the committed catalogue cannot drift.

## Tools — exactly one each

| Tool | Path |
| --- | --- |
| Installer | `scripts/install.sh` |
| Validator (aggregate) | `scripts/validate.py` |
| Catalogue generator | `scripts/gen-catalog.mjs` |
| Index builder | `scripts/build-index.py` |
| Per-skill validator | `scripts/validate_skill.py` |
| Multi-skill validator | `scripts/validate_skills.py` |

No second installer, validator or catalogue generator exists in the tree.

## Status / handoff docs: none

- No `STATUS.md`, `HANDOFF*.md`, `GAPS*.md`, `R3_PLAN.md`, `REVERIFY*.md`, `*.log`,
  `state.json` or `*.db` is committed at the repository root or under `docs/`.
- Proof: `git ls-files | grep -c STATUS` → **0**.
- Proof: `git ls-files | grep -cE '(HANDOFF|GAPS|R3_PLAN|REVERIFY)'` → **0**.
- The only remaining `EVALS.md` files are **skill content**, not diaries: each of the
  30 skills ships `references/EVALS.md` with its eval prompts, and
  `scripts/validate_skills.py` fails a skill that lacks one. They stay.
- A skill's `references/handoff.md` is likewise skill content (the hand-off contract
  of `browser-agent-playwright`, linked from its `SKILL.md`).

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
tests/           # repository-level tests
```

Root `*.md` files: AGENTS.md CONTRIBUTING.md README.md
No stray `.md`, `.log`, `.out`, `state.json` or `*.db` beyond that list.

## Follow-up (not deleted here)

Package-level documents that are neither status diaries nor named by the delete list
of this task stay for the canonical-skills job to judge: skills/agentic-data/AUDIT.md skills/agentic-data/README.md skills/agentic-data/RESEARCH.md skills/agentic-data/browser-agent-playwright/SKILL.md skills/agentic-data/computer-use-drivers/SKILL.md skills/agentic-data/dedup-decontam/SKILL.md skills/agentic-data/deep-research-method/SKILL.md skills/agentic-data/llm-judge-calibration/SKILL.md skills/agentic-data/mcp-2026-07-28/SKILL.md skills/agentic-data/polite-crawling-warc/SKILL.md skills/agentic-data/skill-authoring-evals/SKILL.md skills/agentic-data/trajectory-ledger/SKILL.md skills/agentic-data/verifiable-environments/SKILL.md skills/business-de/PASS3_VERIFY.md skills/business-de/PASS5_GATE.md skills/business-de/README.md skills/business-de/RESEARCH.md skills/business-de/bank-reconciliation-camt/SKILL.md skills/business-de/carrier-apis-de/SKILL.md skills/business-de/datev-extf/SKILL.md skills/business-de/dsgvo-ai-act-labeling/SKILL.md skills/business-de/gobd-archive/SKILL.md skills/business-de/publish-reconcile-wp-meta/SKILL.md skills/business-de/skr-journal-mapping/SKILL.md skills/business-de/ust-edge-cases/SKILL.md skills/business-de/webhooks-safe/SKILL.md skills/business-de/xrechnung-zugferd/SKILL.md skills/community/README.md skills/core/work-untill-i-die/SKILL.md skills/curated/cursor-cli/SKILL.md skills/engineering/README.md skills/engineering/RESEARCH.md skills/engineering/VERIFICATION.md skills/engineering/acceptance-harness/SKILL.md skills/engineering/foundation-v2-conformance/SKILL.md skills/engineering/honest-status/SKILL.md skills/engineering/long-test-discipline/SKILL.md skills/engineering/module-contract-first/SKILL.md skills/engineering/outbox-idempotency/SKILL.md skills/engineering/pg-rls-multitenant/SKILL.md skills/engineering/playwright-a11y-e2e/SKILL.md skills/engineering/problem-json-contracts/SKILL.md skills/engineering/shared-tree-git/SKILL.md skills/orchestrator-preamble/orchestrator-preamble/SKILL.md skills/ottili-ai/README.md skills/ref-bank-reconciliation-camt/ref-bank-reconciliation-camt/SKILL.md skills/ref-datev-extf/ref-datev-extf/SKILL.md skills/ref-gobd-archive/ref-gobd-archive/SKILL.md skills/ref-ust-edge-cases/ref-ust-edge-cases/SKILL.md skills/ref-webhooks-safe/ref-webhooks-safe/SKILL.md skills/ref-xrechnung-zugferd/ref-xrechnung-zugferd/SKILL.md
See `docs/gaps/SKL-W0-01.md` (G19).
