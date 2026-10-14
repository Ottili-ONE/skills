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
| **Quarterly** | Cross-link graph: `python3 scripts/check_related_graph.py --skills skills/engineering` | Circular edges sneak in when two skills are edited in the same pass. |

## Status of the ten skills (as of 2026-10-14, pass 5 of 5)

All ten validate green against the agentskills.io standard (`validate_skill.py --all`) and the
catalog (`validate.py`). Every `EVALS.md` has ≥5 prompts and ≥3 near-miss prompts. The
`## Related skills` graph is acyclic with `shared-tree-git` as the unique sink.

### Pass 5 (evals, validation, cross-links, handoff) findings and repairs

| Area | Defect found | Repair |
|------|--------------|--------|
| EVALS heading format | `long-test-discipline`, `pg-rls-multitenant`, `playwright-a11y-e2e` used a unicode em-dash after the number (`## 1. — ...`), which the `PROMPT_RE` regex (`^##\s+(?:E\d+|\d+)\b`) does not match — the completeness test counted 0 prompts while the file had 6. | Rewrote all headings to `## N. — ...` (ASCII hyphen) in the three files; counts now 6/6/5. |
| Trigger precision | `honest-status` fired for changelogs and chat updates. | Sharpened triggers: scope to work ledgers another agent will pick up; added explicit changelog/chat NOT-use bullets. |
| Version-sensitive facts | `honest-status/SKILL.md` VERIFIED example claimed "axe version bump blocked until registry returns 4.15" — axe-core is at 4.14.0 (re-fetched 2026-10-14), so 4.15 is not yet released. | Reworded the blocker to name the integrator and the live registry URL; removed the false version claim. |
| Cross-link graph | No automated check existed; circular edges could ship silently. | Added `scripts/check_related_graph.py` (DFS cycle detection + link-target resolution); run green on all ten. |
| README / HANDOFF | Missing entirely from this pass's acceptance criteria. | Wrote `skills/engineering/README.md` (one-line value per skill, install hints, related-skill map) and rewrote this `HANDOFF.md` with the pass-5 log. |
| Re-verification of versions | pytest 9.1.1, axe-core 4.14.0, Playwright 1.64.1, @ottili/foundation-ui 1.0.13, PG 18.6 all re-fetched live on 2026-10-14; `agentskills.io` returns 308 (redirect), WCAG page returns 200. | Recorded in each skill's `references/SOURCES.md` under "Re-verification 2026-10-14". |

Re-verification commands (all green on 2026-10-14):

```
python3 scripts/validate_skill.py --all
python3 scripts/validate.py
python3 skills/engineering/tests/test_research_design_acceptance.py
python3 skills/engineering/tests/test_evals_completeness.py
python3 scripts/check_related_graph.py --skills skills/engineering
for f in skills/engineering/*/scripts/*_test.py; do python3 "$f"; done
```
