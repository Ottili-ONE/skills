# Ottili Engineering Playbook Skills

Ten Agent Skills (agentskills.io standard) for coding and operations agents working on
the Ottili platform. Each skill is concrete: decision procedures, checklists with
pass/fail criteria, pitfalls from real incidents, copy-paste-safe commands, and a
verification section. No generic advice.

## Install

```
python3 scripts/install.sh skills/engineering
```

Or copy a single skill folder into any agent-skills directory. Each skill is
self-contained: `SKILL.md` (front matter + body), `references/` (EVALS.md, SOURCES.md,
procedure docs), and optionally `scripts/`.

## Skills

| Skill | One-line value |
| --- | --- |
| `acceptance-harness` | Run an acceptance gate before claiming done: definition-of-done checklist, evidence capture, residual-risk log. |
| `foundation-v2-conformance` | Verify Foundation v2 UI contracts: design tokens, component API, a11y keys, responsive breakpoints. |
| `honest-status` | Write status that is checkable: what works (with evidence), what is stubbed, what is missing — never "done" without a probe. |
| `long-test-discipline` | Design and run tests that finish in minutes, not hours: timeouts, idempotent fixtures, heavy-command orchestration. |
| `module-contract-first` | Derive module boundaries from an explicit contract table (props, events, errors) before writing implementation. |
| `outbox-idempotency` | Make outbox writes exactly-once: dedupe keys, idempotent consumers, transactional outbox pattern. |
| `pg-rls-multitenant` | Enforce tenant isolation in PostgreSQL with Row-Level Security policies and per-tenant quotas. |
| `playwright-a11y-e2e` | End-to-end tests that cover behaviour *and* accessibility with Playwright + axe, including visual regression. |
| `problem-json-contracts` | Design and validate Problem Details (RFC 9457) error contracts with examples and schema. |
| `shared-tree-git` | Operate a shared git worktree safely: lock, fetch, branch hygiene, conflict resolution, merge discipline. |

## Related skills

- `shared-tree-git` is a prerequisite for `acceptance-harness` when the acceptance gate
  runs in a shared repository.
- `problem-json-contracts` and `module-contract-first` both define error contracts;
  use `problem-json-contracts` for HTTP API errors and `module-contract-first` for
  in-process module boundaries.
- `pg-rls-multitenant` and `outbox-idempotency` both touch transactional integrity;
  combine them when a tenant-scoped outbox crosses a database boundary.
- `playwright-a11y-e2e` and `foundation-v2-conformance` both check UI conformance;
  run the e2e suite after the conformance gate passes.

## Pass 3 (2026-10-14) status

All ten skills validate green on `scripts/validate_skills.py` (agentskills.io standard) and
`scripts/validate.py` (catalog). Every `EVALS.md` carries >=5 prompts and >=3 near-miss
prompts (`tests/test_evals_completeness.py`), every `SOURCES.md` carries a dated line
<=180 days old (`tests/test_sources_freshness.py`), and the Related graph is acyclic with
`shared-tree-git` as the unique sink (`scripts/check_related_graph.py`).

Repairs this pass (pass 3 of 3, test + fix):

| Area | Defect found | Repair |
|------|--------------|--------|
| Boilerplate duplication | Seven of ten EVALS.md files repeated one "What the skill changes vs no skill" sentence across every prompt, so the evals read as a template rather than per-scenario contrasts. | Rewrote all 37 duplicated sentences so each states what the skill changes *for that scenario*; the boilerplate is now unique per prompt everywhere. |
| Truncated near-miss prompts | `honest-status` N8 ended mid-sentence and N9 was a fragment ("no — a path that does not resolve..."). | Completed N8 and N9; near-miss count is 11. |
| Duplicate prompt headings | `foundation-v2-conformance` E6 repeated E3's prompt text; `playwright-a11y-e2e` N7/N8 duplicated N1/N2. | Gave each its own prompt and its own near-miss angle; near-miss blocks renumbered N1-N10 with no duplicate text. |
| Fabricated version | `foundation-v2-conformance` E5/N5 cited "Foundation v2.4.1"; the registry's latest is 1.0.13 (re-fetched 2026-10-14). | Reworded to the real latest and recorded the re-fetch in SOURCES.md. |
| Fabricated version gate | `honest-status` SKILL.md BLOCKED example claimed an axe bump was "blocked until the registry returns 4.15"; axe-core is at 4.14.0 (re-fetched 2026-10-14), so 4.15 is not a live question. | Reworded the gate to name the integrator and the `docs/STATUS_ALL.md` artifact that would authorize the bump, and added a pitfall against naming a version that does not exist. |
| Stale retrieval dates | `honest-status`, `outbox-idempotency`, `foundation-v2-conformance`, `module-contract-first` EVALS.md carried 2026-10-13 dates. | Refreshed to 2026-10-14 (pass 3 re-verification). |
| Source freshness | Re-fetched live on 2026-10-14: axe-core 4.14.0, Playwright 1.64.1, `@ottili/foundation-ui` 1.0.13, WCAG 2.2, PG logging docs, agentskills.io, RFC 9457, OpenAPI 3.1.0 — all HTTP 200, no version moved. | Recorded in each affected SOURCES.md. |

## How to verify this pass

Every check is offline and deterministic; run all of them before claiming the
playbook changed:

```
python3 scripts/validate_skills.py                    # agentskills.io standard
python3 scripts/validate.py                           # catalog consistency
python3 skills/engineering/tests/test_evals_completeness.py      # >=5 prompts, >=3 near-misses
python3 skills/engineering/tests/test_sources_freshness.py       # dated SOURCES, <=180 days old
python3 skills/engineering/tests/test_collection_acceptance.py   # RESEARCH + DESIGN + EVALS
python3 skills/engineering/tests/test_research_design_acceptance.py
python3 scripts/check_related_graph.py                # Related graph is acyclic
for t in skills/engineering/*/scripts/*_test.py; do python3 "$t"; done   # every checker self-tests
```

Each skill's own checker also runs against its `references/examples/` fixtures:
the good file exits 0, every bad file exits 1 with findings.

## Cross-links

The `Related skills` section of every SKILL.md forms a **directed graph** with
`shared-tree-git` as the unique sink (every other skill links to it, it links to
nothing). `scripts/check_related_graph.py` verifies the graph is acyclic. The
edges are informational mentions, not runtime dependencies — a skill works
without its Related neighbours being present.

Re-verify a skill with the self-test its `scripts/` folder ships (each skill has one).
