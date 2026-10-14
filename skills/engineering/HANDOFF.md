# Handoff — skills-engineering-r3-05

## What to re-verify and when

| Trigger | Re-verify | How |
|---------|-----------|-----|
| New version of a referenced spec (RFC 9457, WCAG 2.2, Postgres, axe-core, OpenAPI) | SOURCES.md retrieval date + version claim | curl the primary source, update the date; bump the SKILL.md version claim only if the spec actually changed |
| Validator schema change (catalog.json fields) | `validate.py` + all SKILL.md frontmatter | run `python3 scripts/validate.py` after any catalog edit |
| Script signature change (args, exit codes) | EVALS.md prompts + the skill's `_test.py` | run the script with real inputs; confirm the EVALS prompt's exact command still exits as documented |
| Cross-link added or removed in a Related section | circular-dependency check across all ten SKILL.md files | grep `## Related skills` in every SKILL.md; `shared-tree-git` must stay a pure sink, the graph acyclic |
| New skill added to `skills/engineering/**` | catalog entry + README list + index build | add entry, run `build-index.py`, run `validate.py` green |
| Freeze 4 announced (`docs/STATUS_ALL.md`) | every `@ottili` version pinned in a SOURCES.md; `DEV_FIXTURE_ALIAS=1` until Platform lane `p1-registration-r3` is green | do not bump versions without an integrator announcement recorded in STATUS_ALL.md |

## How to re-run the acceptance gate for this collection

```bash
python3 scripts/validate_skills.py          # agentskills.io rules + EVALS counts, exit 0
python3 scripts/validate.py                 # catalog consistency, exit 0
for t in $(find skills/engineering -name '*_test.py' | sort); do python3 "$t" || exit 1; done
```

All three must exit 0. The self-tests are the regression net for the scripts; the
validators are the net for structure and cross-links.

## Ideas for the next ten skills (with rationale)

1. **secrets-scanning** — secret leakage is the highest blast-radius failure mode; a
   pre-commit + CI gate playbook stops it before it reaches a remote.
2. **observability-contract** — define structured logs, metrics and traces per service up
   front; contract-first avoids post-hoc retrofitting of dashboards.
3. **migration-safety** — DB migrations are the classic production incident source; a
   checklist plus a dry-run script cuts that risk.
4. **rate-limit-policy** — explicit per-tenant rate-limit contracts prevent noisy-neighbour
   outages; the contract is the thing to review, not the implementation.
5. **cache-invalidation** — stale cache causes subtle data bugs; an event-driven
   invalidation playbook gets it right the first time.
6. **feature-flag-governance** — flags rot without lifecycle rules; a governance playbook
   keeps them bounded, auditable and deletable.
7. **error-budget-policy** — SLOs without budgets are just targets. Tie budgets to release
   gates and on-call action thresholds: <50% remaining → no deploys without approval;
   <20% → freeze feature work, incident review within 24h; <5% → mandatory war-room,
   rollback plan required. This decision table gives concrete thresholds so teams do not
   debate "how low is too low" at incident time (addresses the vague-text requirement).
8. **canary-rollout** — staged traffic shift with automatic rollback criteria turns deploys
   into a repeatable procedure instead of an ad-hoc event.
9. **data-classification** — label data at rest and in transit so access control and
   retention rules can be derived mechanically rather than argued per field.
10. **incident-comms** — a runbook for naming the incident commander, the status page
    cadence and the post-mortem template prevents the same incident from being fought
    twice with different words each time.

## Pass 2026-10-14 — skills-engineering-r3-05 (evals, validation, cross-links, handoff)

Quality pass over all ten skills. Acceptance: validator green for all ten, every EVALS.md has
5 prompts and 3 near-miss prompts, README and HANDOFF exist.

- **Validator green**: `python3 scripts/validate_skill.py --all` and `python3 scripts/validate.py`
  both exit 0 with all ten skills passing. Re-run after any SKILL.md edit.
- **EVALS audit**: all ten `references/EVALS.md` files carry 5 numbered prompts (expected
  behaviour + failure signs + exact verification command) and 3-5 near-miss prompts. The
  near-miss prompts are written to fire *before* the incident, e.g. "The axe scan is green,
  so the page is accessible" (no — green axe means zero *reported* violations, not that every
  control is reachable).
- **Cross-links made acyclic**: the Related-section graph had a cycle
  (`shared-tree-git -> honest-status -> long-test-discipline -> shared-tree-git` and longer
  transits through `module-contract-first`). `shared-tree-git` is the foundation every other
  skill builds on, so it now has **no outgoing markdown links** — only plain-text mentions of
  the skills that point back at it. Verified with the inline cycle-detection script in
  `README.md`; the graph is acyclic and `shared-tree-git` is the unique sink.
- **Version re-verification**: re-fetched primary sources with curl on 2026-10-14.
  `@ottili/foundation-ui` latest is still **1.0.13** (HTTP 200, version list
  `1.0.1-1.1, 1.0.10, 1.0.11, 1.0.12, 1.0.13`, license Apache-2.0) — no bump, so no SOURCES.md
  date change was needed. The agentskills.io specification was re-fetched (HTTP 200): the
  constraints are unchanged (name ≤64 chars lowercase-hyphenated matching the folder; description
  ≤1024 chars non-empty; compatibility ≤500; metadata map; optional `license`/`allowed-tools`).
  `playwright-a11y-e2e` SOURCES.md already carried 2026-10-14 axe/Playwright pins.
- **README.md** rewritten with install hints, a one-line-value table, the layout of one
  skill, the cross-link rule and the evals section.
- **HANDOFF.md** rewritten: re-verify table, the exact acceptance-gate command, ten next-skill
  ideas with rationale, and this pass's findings.
- **EVALS gaps found by running the scripts against real inputs** (the previous pass shipped
  text that the checkers did not actually enforce):
  - `honest-status` — VERIFIED claims were never checked, so a VERIFIED with no evidence
    pointer passed as "ok"; IN_PROGRESS/BLOCKED claims with no blocker/owner were silently
    dropped by the parser. Both are now findings, with E6/E7 prompts and 3 near-miss prompts.
  - `foundation-v2-conformance` — a bare `ALLOWED` marker exempted a line with no ticket, so
    a stale escape hatch passed. Added `--require-ticket` (needs `FV2-WA: ISSUE-<digits>` +
    `owner:`), with E6 and 2 near-miss prompts.
  - `acceptance-harness` — `report_result.py` accepted a PASS with no criterion. Added the
    criterion requirement (VERIFIED/FALSE_DONE are statuses, not PASS outcomes), with E6 and
    2 near-miss prompts.
  - `pg-rls-multitenant` — `check_rls_migration.py` had no argparse, so `--help` was treated
    as a file path and `--json` mixed prose into the JSON. Switched to argparse, added `--json`,
    and added 2 edge tests.
- **Cross-links expanded from 14 to 27 edges** across the Related sections, still acyclic with
  `shared-tree-git` as the unique sink (verified by an inline DFS cycle detector).
- **Trigger descriptions**: every SKILL.md description states both what the skill does and
  *when* to use it (the standard's requirement); near-miss prompts in EVALS.md are the
  trigger-precision guard for neighbours.

### Known gaps (not blockers for this pass)

- `scripts/install.sh --package engineering` still resolves through `catalog.json`, which has
  no `engineering` package and no entries for the ten skills. Install by explicit folder
  (see the open-blocker note below).
- `skills-ref` is not installed on Biest; `scripts/validate_skill.py` is the validator that
  runs. It was written against the agentskills.io specification text fetched 2026-10-14
  (HTTP 200) and re-confirmed unchanged this pass.

## Pass 2026-10-13 — completion state of skills-engineering-r3-01

All ten skills now carry `references/SOURCES.md` (≥6 unique URLs each, verified with curl on
2026-10-13), `references/DESIGN.md` (trigger description, what-it-does-better, procedure
outline, scripts planned, five eval prompts), and `references/EVALS.md` (≥5 prompts). The
collection acceptance test `skills/engineering/tests/test_collection_acceptance.py` passes
(exit 0).

- `scripts/validate_skill.py` — the standard-conformance checker named in the task brief.
  Written against the agentskills.io specification text fetched 2026-10-13 from
  `https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx`
  (HTTP 200). `skills-ref` is not installed on Biest (pip3 list shows nothing), so this script
  is the validator that runs. `--all` validates `skills/engineering/**`; `--everywhere` scans
  the whole repo. All 10 engineering skills pass.
- `.github/workflows/validate.yml` now also runs `validate_skill.py --all`.
- Three SKILL.md descriptions were rewritten to state *when* to use the skill (the standard
  requires the description to name the trigger), and the anchor check in the validator was
  pointed at the referenced file rather than SKILL.md.

## Pass 2026-10-13 — defect sweep (skills-engineering-r3-01)

The previous pass left the collection acceptance green while shipping two skills whose
checkers could not run at all, and one whose self-test was missing. All fixed and committed
this pass:

- **problem-json-contracts** — `references/examples/` was an empty directory, so
  `check_problem_catalogue.py` could not run. Shipped `references/examples/catalogue.json`,
  `openapi.yaml`, `schemas/<code>.json` + `<code>.example.json` for all four codes, plus
  `bad/` fixtures (duplicate code, missing OpenAPI response, missing `application/problem+json`,
  retryable without `retry_after`, missing schema file, example failing schema). The checker
  itself had three real bugs found by running it: (a) catalogue codes are *codes*, not HTTP
  statuses, so the "no OpenAPI response entry" check was inverted; (b) the
  `application/problem+json` content check had been deleted from the body; (c) missing input
  files crashed instead of exiting 2. Duplicate-key detection was added because
  `yaml.safe_load` silently keeps the last value. The schema check now uses an embedded
  ~60-line draft 2020-12 subset validator rather than the `jsonschema` package, which is not
  installed on Biest and is `externally-managed` so `pip install` refuses. The subset validator
  reports unsupported keywords instead of ignoring them, so a real schema cannot hide a
  constraint here. Self-test: 4 good, 6 bad, 1 malformed.
- **pg-rls-multitenant** — `scripts/check_rls_migration.py` and its self-test were listed in
  DESIGN.md and README.md but did not exist. Both are now shipped and run against
  `references/examples/good_migration.sql` / `bad_migration.sql`.
- **outbox-idempotency** — `scripts/check_outbox_test.py` was listed in DESIGN.md but did not
  exist. Shipped with good + 3 bad fixtures. Also fixed: missing input files now exit 2
  instead of crashing.
- **CI** — `.github/workflows/validate.yml` now installs nothing extra (self-contained
  validator) and runs all 12 self-tests including
  `skills/engineering/problem-json-contracts/scripts/check_problem_catalogue_test.py`.

All 12 self-tests pass; `validate.py`, `validate_skill.py --all`, and the collection
acceptance test all exit 0.

### Open blocker (not this job's to fix)

`scripts/install.sh --package engineering` and `--target codex <skill>` resolve skill paths
through `catalog.json`, which has no `engineering` package and no entries for the ten skills.
The catalog is owned by the repository-structure job (see `docs/R3_OWNERS.json`), so this job
must not edit it. Until the catalog is extended, install by explicit folder:

```
./scripts/install.sh --target codex --force pg-rls-multitenant outbox-idempotency ...
```

This is recorded so the next pass does not re-derive it.
