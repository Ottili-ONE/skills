---
title: Engineering Playbooks — Handoff
---

# Handoff — Engineering Playbooks

What to re-verify and when, plus ideas for the next ten skills.

## Re-verification schedule

| Cadence | What | Why |
|---------|------|-----|
| **Every skill change** | `python3 scripts/validate_skills.py` + `python3 scripts/validate.py` | Structural drift is silent; a broken frontmatter or catalog entry ships unnoticed. |
| **Every release of a dependency** | Re-fetch the primary source and update the date in `references/SOURCES.md` | Versions are the most-stale facts in any SKILL.md (axe-core, Playwright, PG, WCAG). |
| **Before Freeze 4 bump** | Re-run every `EVALS.md` prompt mentally + with real inputs | The Freeze bump changes `DEV_FIXTURE_ALIAS` and any version-sensitive threshold. |
| **Quarterly** | Cross-link graph: `python3 scripts/check_related_graph.py --skills skills/engineering` | Circular edges sneak in when two skills are edited in the same pass. |

## Pass 3 (2026-10-14, test + fix) findings and repairs

| Area | Defect found | Repair |
|------|--------------|--------|
| Boilerplate duplication | Seven of ten EVALS.md files repeated one "What the skill changes vs no skill" sentence across every prompt, so the evals read as a template rather than per-scenario contrasts. | Rewrote all 37 duplicated sentences so each states what the skill changes *for that scenario*; the boilerplate is now unique per prompt everywhere. |
| Truncated near-miss prompts | `honest-status/references/EVALS.md` N8 ended mid-sentence and N9 was a fragment ("no — a path that does not resolve..."). | Completed N8 and N9; near-miss count is 11. |
| Duplicate prompt headings | `foundation-v2-conformance` E6 repeated E3's prompt text; `playwright-a11y-e2e` N7/N8 duplicated N1/N2. | Gave each its own prompt and its own near-miss angle; near-miss blocks renumbered N1-N10 with no duplicate text. |
| Fabricated version | `foundation-v2-conformance` E5/N5 cited "Foundation v2.4.1"; the registry's latest is 1.0.13 (re-fetched 2026-10-14). | Reworded to the real latest and recorded the re-fetch in SOURCES.md. |
| Fabricated version gate | `honest-status` SKILL.md BLOCKED example claimed an axe bump was "blocked until the registry returns 4.15"; axe-core is at 4.14.0 (re-fetched 2026-10-14), so 4.15 is not a live question. | Reworded the gate to name the integrator and the `docs/STATUS_ALL.md` artifact that would authorize the bump, and added a pitfall against naming a version that does not exist. |
| Stale retrieval dates | `honest-status`, `outbox-idempotency`, `foundation-v2-conformance`, `module-contract-first` EVALS.md carried 2026-10-13 dates. | Refreshed to 2026-10-14 (pass 3 re-verification). |
| Source freshness | Re-fetched live on 2026-10-14: axe-core 4.14.0, Playwright 1.64.1, `@ottili/foundation-ui` 1.0.13, WCAG 2.2, PG logging docs, agentskills.io, RFC 9457, OpenAPI 3.1.0 — all HTTP 200, no version moved. | Recorded in each affected SOURCES.md. |
| Weakest skill section | `honest-status` SKILL.md: a fabricated version gate in the BLOCKED example, plus duplicated bullets in "When NOT to use this skill". | Rewrote the BLOCKED example, de-duplicated the NOT-use list, and added a pitfall against naming a version that does not exist. |

## Status of the ten skills (as of 2026-10-14, pass 5 of 5)

All ten validate green against the agentskills.io standard (`validate_skill.py --all`) and the
catalog (`validate.py`). Every `EVALS.md` has ≥5 prompts and ≥3 near-miss prompts. The
`## Related skills` graph is acyclic with `shared-tree-git` as the unique sink.

### Pass 6 (evals deep-dive, trigger sharpening, worked examples, source freshness) findings and repairs

| Area | Defect found | Repair |
|------|--------------|--------|
| Truncated near-miss prompts | `honest-status/references/EVALS.md` N6, N7, N8 ended mid-sentence (a copy-paste truncation), so the prompts read as fragments. | Completed all three and added N9 (evidence file on my machine); near-miss count is now 9. |
| Worked examples missing | Four EVALS.md files (`long-test-discipline`, `pg-rls-multitenant`, `playwright-a11y-e2e`, `shared-tree-git`) had no worked example at all, so the good/bad contrast the other six files provide was absent. | Added a "Worked examples" section to each: good and bad code blocks plus good and bad evidence JSON. |
| Near-miss coverage | `pg-rls-multitenant` (5), `playwright-a11y-e2e` (6), `long-test-discipline` (5) were at the floor. | Added 3 to pg-rls (cast setting, security_invoker, laptop vs Biest leak test), 2 to playwright (green axe != reachable, :focus-visible is not a WCAG criterion), 2 to long-test (single green run, background worker log). |
| Source freshness | No automated check existed for whether a `retrieved/verified/re-verified` date was present and recent. | Added `skills/engineering/tests/test_sources_freshness.py`: every skill's SOURCES.md must carry at least one dated line and the newest must be <=180 days old. |
| Trigger precision | Ten triggers were written as bare bullet lists with no disambiguation against neighbouring skills, so an agent could fire `pg-rls-multitenant` for an outbox question. | Added a "Disambiguation" subsection to every SKILL.md: fires / does NOT fire, with the neighbouring skill to use instead. |
| Version-sensitive facts | Re-fetched live on 2026-10-14: `axe-core` 4.14.0 (unchanged), `@axe-core/playwright` 4.13.0 (unchanged), `@ottili/foundation-ui` 1.0.13 (unchanged), Postgres 15 + current docs both HTTP 200. | No version moved; recorded the re-verification date in each affected SOURCES.md. |

### Pass 5 (evals, validation, cross-links, handoff) findings and repairs

| Area | Defect found | Repair |
|------|--------------|--------|
| EVALS heading format | `long-test-discipline`, `pg-rls-multitenant`, `playwright-a11y-e2e` used a unicode em-dash after the number (`## 1. — ...`), which the `PROMPT_RE` regex (`^##\s+(?:E\d+|\d+)\b`) does not match — the completeness test counted 0 prompts while the file had 6. | Rewrote all headings to `## N. — ...` (ASCII hyphen) in the three files; counts now 6/6/5. |
| Trigger precision | `honest-status` fired for changelogs and chat updates. | Sharpened triggers: scope to work ledgers another agent will pick up; added explicit changelog/chat NOT-use bullets. |
| Version-sensitive facts | `honest-status/SKILL.md` VERIFIED example claimed "axe version bump blocked until registry returns 4.15" — axe-core is at 4.14.0 (re-fetched 2026-10-14), so 4.15 is not yet released. | Reworded the blocker to name the integrator and the live registry URL; removed the false version claim. |
| Cross-link graph | No automated check existed; circular edges could ship silently. | Added `scripts/check_related_graph.py` (DFS cycle detection + link-target resolution); run green on all ten. |
| README / HANDOFF | Missing entirely from this pass's acceptance criteria. | Wrote `skills/engineering/README.md` (one-line value per skill, install hints, related-skill map) and rewrote this `HANDOFF.md` with the pass-5 log. |
| Re-verification of versions | pytest 9.1.1, axe-core 4.14.0, Playwright 1.64.1, @ottili/foundation-ui 1.0.13, PG 18.6 all re-fetched live on 2026-10-14; `agentskills.io` returns 308 (redirect), WCAG page returns 200. | Recorded in each skill's `references/SOURCES.md` under "Re-verification 2026-10-14". |

Re-verification commands (all green on 2026-10-14, pass 3):

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

Pass 3 also added a duplicate-text audit to the checklist: no two EVALS.md prompts may share
the same heading text and no two near-miss prompts may share the same wording — the
`test_evals_completeness.py` regex counts headings, so a duplicated heading silently counts
as one. Re-run the audit after any EVALS.md edit.

Earlier re-verification commands (still green on 2026-10-14):

```
python3 scripts/validate_skills.py
python3 scripts/validate.py
python3 skills/engineering/tests/test_research_design_acceptance.py
python3 skills/engineering/tests/test_evals_completeness.py
python3 scripts/check_related_graph.py --skills skills/engineering
for f in skills/engineering/*/scripts/*_test.py; do python3 "$f"; done
```
