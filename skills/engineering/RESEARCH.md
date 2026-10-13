# skills-engineering-r3 — Research & Design Index

Job: `skills-engineering-r3` (Ten engineering playbook skills for Ottili agents).
Research pass: 2026-10-12. Host: Biest. SEARCH_ENDPOINT: none — all URLs below were fetched
directly with curl and recorded in each skill's `references/SOURCES.md`.

## Ranked list and final names

No seed topic was replaced. All ten seed topics map 1:1 to a final skill because each maps to a
concrete, verifiable failure mode in the Ottili system map (`../ottili-planning/system-map/`):

| # | Seed topic | Final name | Why it ranks here |
|---|-----------|-----------|-------------------|
| 1 | pg-rls-multitenant | `pg-rls-multitenant` | Tenant isolation is the platform's core safety property; a leak is a P1 incident. |
| 2 | outbox-idempotency | `outbox-idempotency` | Ottili runs many integrations (DHL, DATEV, Keycloak); duplicate messages are the most common production defect. |
| 3 | problem-json-contracts | `problem-json-contracts` | Every API surface in the system map returns RFC 9457 problems; agents must emit and consume them correctly. |
| 4 | module-contract-first | `module-contract-first` | Four agents share one working tree; module boundaries are the only thing preventing cross-module breakage. |
| 5 | shared-tree-git | `shared-tree-git` | Direct consequence of (4): git discipline for many agents, one repo. |
| 6 | long-test-discipline | `long-test-discipline` | E2E/integration tests take minutes; a shared host kills unmanaged background processes. |
| 7 | playwright-a11y-e2e | `playwright-a11y-e2e` | Foundation UI must be keyboard-accessible and axe-clean; agents must not write selectors that break. |
| 8 | foundation-v2-conformance | `foundation-v2-conformance` | The Foundation packages are the single UI dependency; using them wrong is the most common UI defect. |
| 9 | acceptance-harness | `acceptance-harness` | Scenarios need PASS/FAIL/BLOCKED semantics and fault injection to be meaningful. |
| 10 | honest-status | `honest-status` | STATUS.md is the handoff artifact; false "done" is the highest-risk output of all. |

## Replacements considered and rejected

- **"shared-tree-git" → "multi-agent-git"**: rejected. The seed name is more concrete and matches
  the actual constraint (one working tree, not just "many agents").
- **"problem-json-contracts" → "error-contracts"**: rejected. RFC 9457 is the *mechanism*, not the
  concept; keeping the RFC name forces precision.
- **"foundation-v2-conformance" → "foundation-ui"**: rejected. Conformance (with workaround markers
  and fresh-consumer tests) is the hard part the skill teaches; "UI" is too vague.

## Cross-cutting decisions

1. Every skill uses the same structure: `SKILL.md` (front matter + body ≤ 500 lines / ~5,000 tokens)
   plus `references/SOURCES.md`, `references/DESIGN.md`, `references/EVALS.md`, and a `scripts/`
   folder when the skill ships a runnable tool. Long material lives in `references/*.md` linked one
   level deep from SKILL.md (progressive disclosure per the agentskills.io standard).
2. Every skill's `references/SOURCES.md` records ≥ 6 primary sources with URL + retrieval date,
   conflicts between sources, and version-sensitive facts pinned to the version verified.
3. Every skill's `references/EVALS.md` has ≥ 5 realistic test prompts with expected behaviour and
   failure signs.
4. Quality bar per skill: concrete decision procedures, checklists with pass/fail criteria,
   pitfalls from real incidents, copy-paste-safe commands, good/bad output examples, and a
   verification section. No generic advice, no marketing text.
5. Root artifacts (`README.md`, `scripts/validate.py`, `scripts/install.sh`,
   `scripts/build-index.py`, `AGENTS.md`) are committed first, then the ten skills.
6. `scripts/validate_skill.py` (added 2026-10-13) is the standard-conformance checker named
   in the task brief. It was written against the agentskills.io specification text fetched
   2026-10-13 from
   `https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx`
   (HTTP 200) — the primary source for name rules (≤64 chars, lowercase-hyphenated, must equal
   the folder name), the 1024-char description limit, the ≤500-char `compatibility` field, and
   the ≤500-line SKILL.md guidance. `skills-ref` is not installed on Biest (pip3 list shows
   nothing), so this script is the validator that runs. It defaults to `skills/engineering/**`
   and gains `--everywhere` for a whole-repo scan. CI runs it in `.github/workflows/validate.yml`.
