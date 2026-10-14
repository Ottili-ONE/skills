# STATUS — browser-agent-playwright — 2026-10-14

Scope: `skills/agentic-data/browser-agent-playwright/` (skill 4 of 10, agentic-data lane).
Task: `skills-agentic-data-r3-03` (build skills 4-6).

## Deliverables claimed in the task prompt
- `SKILL.md` — front matter name == folder, description <=1024 chars, body <500 L.
- `references/` — DESIGN, EVALS, SOURCES, decision-tables, handoff, injection-decision,
  injection-defense, locator-catalog, network-waits, procedures.
- `scripts/` — sanitize.py, handoff.py, gen_hostile.py, validate_skill.py.
- `tests/` — test_sanitize.py, test_handoff.py, test_roundtrip.py.
- `references/EVALS.md` — 11 prompts (>=5 required) with expected behaviour + failure signs.

## Verification run this pass (2026-10-14, PASS 4 / r3-03 close-out)
1. `python3 -m pytest skills/agentic-data/browser-agent-playwright/ -q` -> **22 passed**, 0 failed.
2. `python3 skills/agentic-data/scripts/acceptance_check.py` -> **ACCEPTANCE: PASS**;
   browser rows: name == folder, description 365 chars, links resolve one level deep,
   SOURCES 12 URLs, DESIGN has trigger/procedure/scripts/evals, EVALS 11 prompts,
   SKILL.md 126 lines.
3. Per-skill validator: `scripts/validate_skill.py` -> **PASS: browser-agent-playwright
   validates against the Agent Skills standard**.
4. Script smoke (all four scripts, `--help`, exit 0): sanitize, handoff, gen_hostile,
   validate_skill.
5. Live re-fetch of version-sensitive primary URLs (curl, 2026-10-14) — see SOURCES.md
   "Re-verification 2026-10-14 (PASS 4 / r3-03 close-out)". All 6 returned HTTP 200.
   **New fact this pass: PyPI reports Playwright latest = 1.64.0** (upload
   2026-10-13T23:35:20Z), up from 1.63.0. The SKILL.md front matter and the
   `compatibility:` line were updated to 1.64.0; the `>=1.49` pin is unchanged and
   now conservative by ~15 minor releases. The locator API surface was re-grepped
   byte-identical in the live docs (getByRole 32, getByLabel 5, getByTestId 9,
   getByText 14, getByAltText 3, getByTitle 5, getByPlaceholder 3, locator.first 3,
   locator.last 2, locator.nth 2, filter 30, evaluateAll 2; page API: frameLocator 5,
   waitForLoadState 6, addInitScript 6, route 56, waitForEvent 7).

## What works
- Three-tier invariant enforced in code: every action grounded (typed locator), every
  wait web-first (no fixed sleep), every page text treated as untrusted data.
- Locator priority order role > labelled > testid > text > css > xpath is enforced by
  `scripts/sanitize.py --check` (exit 1 on `page.getByText` used as primary) and by the
  locator-catalog reference.
- Injection severity is a decision table: `exfil:`/`encoding:`/`instruction:` = HIGH
  (refuse, quote as evidence, tell the user); `typoglycemia:` = MEDIUM (proceed but
  quote and flag); none = clean. A bare "ignore previous instructions" string is HIGH
  because it is a direct instruction override, not a spelling quirk.
- Best-of-N jailbreak cap: 50 attempts per task, 300 per hour, enforced by
  `scripts/handoff.py` flags.
- Hand-off contract: `build()` returns an `_error` dict on any failure, never `None`
  (the near-miss that crashed a prior round); the summary is emitted with locators
  still live, then the context is closed in a `finally` block.
- Hostile-fixture generator (`gen_hostile.py`) is deterministic (seeded) and drives the
  round-trip probe in `tests/test_roundtrip.py`.

## What is stubbed / missing
None. All scripts run offline; all 22 tests pass; the validator finds 0 problems;
11 eval prompts with expected behaviour and failure signs are shipped.

## Acceptance verdict
**PASS.** The skill validates, scripts run offline, EVALS exist (11 prompts), the
SKILL.md body is 126 lines (<500), and every version-sensitive fact is marked with the
version and date it was verified (Playwright 1.64.0, 2026-10-14). No push, no history
rewrite, no paths outside `skills/agentic-data/browser-agent-playwright/**` touched
this pass.
