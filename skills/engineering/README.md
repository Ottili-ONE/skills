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

Repairs this pass: the `honest-status` EVALS.md repeated one boilerplate sentence across
five prompts — each now states what the skill changes *for that scenario*; two SOURCES.md
entries were re-fetched live and the retrieval date recorded.

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

See `HANDOFF.md` for what to re-verify and when.
