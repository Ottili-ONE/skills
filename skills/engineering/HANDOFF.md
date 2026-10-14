---
title: Engineering Playbooks — Handoff
---

# Handoff — Engineering Playbooks

What to re-verify and when, plus ideas for the next ten skills.

## Re-verification schedule

| Cadence | What | Why |
|---------|------|-----|
| **Every skill change** | `python3 scripts/validate_skill.py --all` + `python3 scripts/validate.py` | Structural drift is silent; a broken frontmatter or catalog entry ships unnoticed. |
| **Every release of a dependency** | Re-fetch the primary source and update the date in `references/SOURCES.md` | Versions are the most-stale facts in any SKILL.md (axe-core, Playwright, PG, WCAG). |
| **Before Freeze 4 bump** | Re-run every `EVALS.md` prompt mentally + with real inputs | The Freeze bump changes `DEV_FIXTURE_ALIAS` and any version-sensitive threshold. |
| **Quarterly** | Cross-link graph: `python3 scripts/check_shared_tree.py scan -- skills/engineering` | Circular edges sneak in when two skills are edited in the same pass. |

## Status of the ten skills (as of 2026-10-14, pass 3 of 3)

All ten validate green against the agentskills.io standard (`validate_skill.py --all`) and the
catalog (`validate.py`). Every `EVALS.md` has ≥5 prompts and ≥3 near-miss prompts. The
`## Related skills` graph is acyclic with `shared-tree-git` as the unique sink.

### Pass 3 (test + fix) findings and repairs

| Area | Defect found | Repair |
|------|--------------|--------|
| problem-json-contracts | The `examples/` catalogue used `retry`/`retryable` inconsistently and shipped no schema/example files for codes `400`/`404`/`409`, so the two documented gates (`check_problem_catalogue.py` and `validate_problem_examples.py`) exited 1 on the shipped examples. | Added `400.json`, `404.json`, `409.json` plus matching `.example.json` files; aligned the catalogue on `retryable`/`retry_after` with `schema` URIs. Both gates now exit 0. |
| acceptance-harness | `make_harness.sh` and `foundation-v2-conformance/scripts/fresh_consumer_test.sh` had unterminated here-docs (`bash -n` warned; the scripts truncated their own output). | Closed both here-docs; verified `make_harness.sh` runs end-to-end on a real input. |
| EVALS structure | `acceptance-harness/EVALS.md` had malformed E4/E5 entries and a duplicated paragraph in E6; `module-contract-first/EVALS.md` had truncated failure-sign lines; `honest-status/EVALS.md` carried a duplicated "What the skill changes" paragraph per prompt; `long-test-discipline/EVALS.md` had a line ending corrupted by a previous search/replace. | Rewrote E4/E5/E6 as properly headed prompts; repaired truncated lines; collapsed duplicates; fixed the corrupted line. |
| Version-sensitive facts | `acceptance-harness/EVALS.md` still claimed "pytest 8.x" (registry returns 9.1.1); `foundation-v2-conformance/SOURCES.md` linked `github.com/ottili/foundation`, which returns **404**. | Re-fetched pytest (9.1.1), foundation-ui (1.0.13), axe-core (4.14.0), Playwright (1.64.1), Postgres (18.6) live on 2026-10-14; replaced the dead GitHub URL with the live npm registry entry and recorded it under Dead / moved URLs. |
| Trigger precision | `long-test-discipline` fired for any test >60s (a 5s smoke test qualifies); `honest-status` fired for changelogs and chat updates. | Sharpened both triggers: long-test now requires minute-scale or flaky/worker/timeout signals; honest-status now scopes to work ledgers another agent will pick up and adds an explicit changelog/chat NOT-use bullet. |
| outbox-idempotency | The NOT-use list duplicated the fire-and-forget bullet. | Deduplicated. |
| module-contract-first | The NOT-use list duplicated the single-file-script bullet and had a confusing pre-release line. | Rewrote as the weakest section of the pass: five distinct, non-overlapping bullets. |

Re-verification commands (all green on 2026-10-14):

```
python3 scripts/validate_skill.py --all
python3 scripts/validate.py
python3 skills/engineering/tests/test_research_design_acceptance.py
python3 skills/engineering/tests/test_evals_completeness.py
for f in skills/engineering/*/scripts/*_test.py; do python3 "$f"; done
```

## Ideas for the next ten skills (with rationale)

1. **`ci-contract-pin`** — Every CI workflow pins its actions to a SHA, not a moving tag. Rationale: moving tags are the most common silent supply-chain drift in Ottili repos.
2. **`secret-scan-gate`** — A pre-commit hook that fails on high-entropy strings in diffs. Rationale: `shared-tree-git` cannot stop another lane from committing a secret; a gate can.
3. **`migration-sequence`** — Enforces migration numbering and that every migration has a `-- ROLLBACK` block. Rationale: `pg-rls-multitenant` requires rollback blocks but has no ordering checker.
4. **`evidence-retention`** — Where logs, screenshots and axe JSON live, for how long, and in which bucket. Rationale: `honest-status` demands evidence but never says where it lives.
5. **`schema-drift-guard`** — Detects when a DB schema diff would break a consumer's contract. Rationale: `module-contract-first` is code-only; schemas need the same treatment.
6. **`outbound-link-checker`** — Weekly crawl of every URL in `references/SOURCES.md`. Rationale: the 60 live-URL check from pass 1 rots every week.
7. **`fixture-frozen`** — Marks test fixtures as immutable and fails edits to them. Rationale: `acceptance-harness` PASS/FAIL/BLOCKED verdicts depend on fixtures not drifting.
8. **`release-notes-discipline`** — Every commit message must map to a CHANGELOG entry. Rationale: `honest-status` statuses need a human-readable trail.
9. **`shadow-dom-traversal`** — A focused sub-skill for Web Components keyboard traversal. Rationale: `playwright-a11y-e2e` mentions shadow DOM but defers the deep recipe.
10. **`shared-tree-merge`** — How two lanes coordinate when their paths genuinely overlap. Rationale: `shared-tree-git` forbids rebase/merge; this skill provides the sanctioned alternative.
