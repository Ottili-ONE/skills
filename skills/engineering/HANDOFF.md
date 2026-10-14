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

## Status of the ten skills (as of 2026-10-14)

All ten validate green against the agentskills.io standard (`validate_skill.py --all`) and the
catalog (`validate.py`). Every `EVALS.md` has ≥5 prompts and ≥3 near-miss prompts. The
`## Related skills` graph is acyclic with `shared-tree-git` as the unique sink.

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
