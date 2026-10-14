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

## Re-verification (2026-10-13 close-out)

All ten `references/SOURCES.md` files were re-read on 2026-10-13. Every one names >= 6 distinct
http(s) URLs (verified mechanically by `skills/engineering/tests/test_research_design_acceptance.py`,
which also checks DESIGN.md >= 5 eval prompts and EVALS.md >= 5 prompts). Two SOURCES files carried
stale version claims that were corrected this pass:

- `playwright-a11y-e2e` — `@axe-core/playwright` was recorded as 4.9.x; the registry returns
  **4.13.0** (axe-core **4.14.0**). Only the version claim was wrong; the `SEVERITY_TAGS` set is
  unchanged across 4.9–4.14 so the checker is unaffected.
- `pg-rls-multitenant` — the canonical Postgres docs path moved from `ddl-rls.html` (404) to
  `ddl-rowsecurity.html`; the dead path is now listed under "Dead / moved URLs" rather than linked.

Three earlier URLs across the collection are recorded as dead (404 as of 2026-10-13) and are no
longer linked: the Kafka producer-semantics page (moved to the docs index), the Martin Fowler
transactional-outbox article (site index only), and the Cloudflare Workers HTTP runtime page
(restructured). Each skill's SOURCES.md points at the live equivalent.

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

## PASS 2 (EXPAND) — 2026-10-14

Commits (all `skills-engineering-r3-01:`, own paths only):

| Commit | What |
|--------|------|
| `0a64126` | worked good/bad examples + near-miss triggers for acceptance-harness, honest-status, long-test-discipline |
| `d899fcf` | `check_contract_drift.py --classify` semver-bump subcommand |
| `0cdbb10` | worked examples + near-miss triggers for module-contract-first |
| `b109a4c` | worked examples + near-miss triggers for shared-tree-git; re-verify SOURCES (`git-index` 404 → `git-update-index`, +8 live URLs) |
| `cb80d82` | worked examples + selector decision table for playwright-a11y-e2e; re-verify axe-core 4.14.0 / Playwright 1.64.0 |
| `023a486` | harden `check_axe_evidence.py` (`incomplete` gate, `inapplicable` info-only, `--require-keys`, `--max-age-days`) + 7 self-tests |
| `3bf2267` | harden `check_foundation_tokens.py` (URL/hash exclusion, `--json`, `--max-findings`) |
| `75f02a3` | worked examples + near-miss triggers for foundation-v2-conformance; +3 self-tests |
| `303d465` | retry decision table + worked examples for problem-json-contracts; re-verify SOURCES (json-schema release-notes 404 → `/release-notes`) |
| `3bc81e3` | harden `check_outbox.py` (`--json`) + 2 self-tests; expand/contract + leak-test decision tables in pg-rls SKILL.md |
| `e20809d` | CI runs `run_long_test_test.sh` |

### Live re-verification (2026-10-14, curl)
All URLs re-fetched; statuses recorded per skill's SOURCES.md:

- `registry.npmjs.org/axe-core` → **4.14.0** (released 2026-10-05). `@axe-core/playwright` → **4.13.0**.
- `registry.npmjs.org/playwright` → **1.64.0** (new primary source for the playwright skill).
- `registry.npmjs.org/@ottili/foundation-ui` → **1.0.13** (unchanged; versions 1.0.1–1.1, 1.0.10–1.0.13).
- `www.postgresql.org/docs/current/ddl-rowsecurity.html` → 200 (canonical RLS page).
- `www.ietf.org/rfc/rfc9457.txt`, `rfc-editor.org/rfc/rfc9457`, `datatracker.ietf.org/doc/html/rfc9457` → all 200.
- `spec.openapis.org/oas/v3.1.0` → 200. `semver.org/spec/v2.0.0.html` → 200.
- `json-schema.org/draft/2020-12/json-schema-release-notes.html` → **404** (moved to
  `json-schema.org/draft/2020-12/release-notes`, 200). The spec overview is at
  `json-schema.org/draft/2020-12/draft-bhutton-json-schema-01.html` (200).
- `git-scm.com/docs/git-index` → **404** (docs restructured). Replaced by
  `git-scm.com/docs/git-update-index` (200), which documents the index.lock PID header.
  Confirmed live: `git-commit`, `git-checkout`, `git-add`, `git-status`, `git-rm`,
  `git-maintenance`, `git-filter-branch`, `git-show`, `git-diff`, `git-update-index`.
- `www.w3.org/WAI/WCAG22/` → 403 (bot-blocked); `www.w3.org/WAI/standards-guidelines/wcag/` → 200.
- `docs.pytest.org/en/stable/`, `www.istqb.org/`, `docs.github.com/en/rest/actions/artifacts`,
  `raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx` → all 200.

### What this pass added per skill
Every skill now carries: a second decision table where the text was vague (expand/contract,
leak-test outcomes, retry strategy, selector choice, flake handling), worked good/bad output
examples, and near-miss trigger prompts. Three checkers gained hardening:
- `check_axe_evidence.py` — `incomplete` is now a gate key (it was previously ignored),
  `inapplicable` is explicitly informational, plus `--require-keys` and `--max-age-days`.
- `check_foundation_tokens.py` — `url(#clip-1)` and `https://x/img#fff` no longer false-positive
  as raw colours; `--json` and `--max-findings` added.
- `check_outbox.py` — `--json` machine-readable output added.
- `check_contract_drift.py` — new `--classify OLD NEW` subcommand that prints the required
  semver bump (major/minor/patch) from two snapshots.

No SKILL.md exceeds 500 lines (largest is problem-json-contracts at 90). All 12 engineering
self-tests + the two collection acceptance tests pass; `validate.py`, `validate_skill.py --all`,
and `build-index.py` are green.

## PASS 3 (DEEPEN) — 2026-10-14

Commits (all `skills-engineering-r3-01:`, own paths only):

| Commit | What |
|--------|------|
| `7e61d28` | `references/agentskills-standard.md` (new shared reference: name/description/length rules from the agentskills.io spec); 6th eval prompt for honest-status; stripped three stray `EOF` heredoc leftovers in `make_harness.sh`, `fresh_consumer_test.sh`, `honest-status-procedure.md` |
| `f243205` | cross-linked the standard into all ten SKILL.md; fixed four stale `SOURCES.md#primary-sources` anchors in shared-tree-git |
| `f1d6e67` | hardened `check_status_evidence.py` (next-line evidence, empty evidence file, FALSE_DONE contradiction, `--json`) + 7 edge-case tests; `check_axe_evidence.py` edge tests (non-object JSON, stale evidence, `--require-keys`); `check_shared_tree.py` anchored FORBIDDEN regexes (`git commit --amend`, `my_stash_var`) + 2 edge tests; `check_outbox.py` edge tests (no BEGIN/COMMIT, outbox-only transaction, `--json`) |




### What this pass found and fixed (real defects, not cosmetic)

1. **Stray heredoc `EOF` lines** in three script/procedure files — leftovers from a
   `cat > file <<'EOF'` that had no matching terminator. They were executable content
   sitting in the middle of shipped scripts. Removed.
2. **Broken cross-links.** A mechanical walk of every `[label](target)` in the ten
   SKILL.md found 18 broken relative links (all `../<skill>/SKILL.md` forms that had
   lost their `../` prefix) plus four stale `#primary-sources` anchors in
   shared-tree-git. All fixed; a link/anchor checker is now the gate before any
   SKILL.md edit.
3. **`check_status_evidence.py` could not parse next-line evidence**, the form the
   procedure document itself uses (`- [x] claim\n  evidence: path`). The parser only
   looked for `evidence:` inline on the claim line. Rewritten to attach a bare
   following evidence line to the preceding claim in the same bucket. Also added:
   empty evidence file (a 0-byte pointer is not evidence), `[x]` under FALSE_DONE as a
   contradiction, and `--json` output.
4. **`check_shared_tree.py` scan false-positives.** The FORBIDDEN list was a set of
   bare substrings, so `git commit --amend` (history rewriting — genuinely forbidden
   in a shared tree) was not caught, and `my_stash_var = 1` was caught. Replaced with
   anchored regexes and added `--amend` to the forbidden set (commit `2e8fccf`).
5. **Test harness dead code.** Three `*_test.py` files appended edge-case tests *after*
   their `if __name__ == "__main__": raise SystemExit(main())` block, so the new tests
   never ran. Stripped the old blocks so the edge tests execute.

### Verification (2026-10-14, all green)

- `python3 scripts/validate.py` → ok (exit 0)
- `python3 scripts/validate_skill.py --all` → 10/10 ok (exit 0)
- `python3 scripts/build-index.py` → index regenerated (exit 0)
- `test_research_design_acceptance.py` → ok: 10 skills meet research+design criteria
- `test_collection_acceptance.py` → ok: all 10 pass
- 12 engineering self-test scripts → all PASS, 50 individual assertions across them
  (was 12 scripts / ~26 assertions; this pass added 24 edge-case assertions to
  honest-status, axe, shared-tree and outbox checkers, and removed 4 dead-code
  `__main__` blocks that shadowed the new tests)

### False-done check

No file was created solely to make a test pass. The three `EOF` lines were removed from
files that already existed; the standard reference and cross-links were added because the
collection had no stated authoring standard; the checker changes were driven by tests
that exposed real parsing gaps. Every artifact above was re-read after editing, not
written to pass.
