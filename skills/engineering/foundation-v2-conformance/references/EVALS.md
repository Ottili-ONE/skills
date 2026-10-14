# EVALS — foundation-v2-conformance
Retrieval date: 2026-10-13. Verified versions: @ottili/foundation-ui 1.0.13
(latest; Apache-2.0). Sources: references/SOURCES.md.

Each prompt lists expected behaviour, failure signs, and what would prove the skill
changed the outcome compared with no skill at all.

## E1 — raw styling literal
**Prompt**: "Add a settings page using the Foundation `Tabs` and `Select` components.
The designer gave me hex colours `#1a1a1a` and `#3a8a6c`."
**Expected**: agent maps the colours to tokens from the Foundation token file, or flags them
as custom and requests a token addition. It does **not** hardcode the hex.
**Failure sign**: agent pastes the hex into styled-components and calls it done.
**What the skill changes vs no skill**: without the skill, a generic agent happily hardcodes
the designer's hex. The skill forces a token lookup and makes a non-token value a defect.

## E2 — deep import
**Prompt**: "The build fails: `Cannot find module '@ottili/foundation-button/dist/index'`."
**Expected**: agent imports from the package root, not the deep path, and checks the version
pin in `package.json`.
**Failure sign**: agent keeps the deep import and adds an `ignore` rule somewhere.
**What the skill changes vs no skill**: the skill knows the package `exports` map is the
contract; a generic agent treats the error as a path problem and "fixes" it by changing the
path, which breaks again on the next version.

## E3 — untracked workaround
**Prompt**: "My PR uses `data-ottili-workaround` to hide a layout bug."
**Expected**: agent requires a ticket reference (`FV2-WA: ISSUE-<digits>`) in the attribute or
the accompanying comment, with an owner and a date, or rejects the workaround.
**Failure sign**: agent accepts the workaround because "it ships".
**What the skill changes vs no skill**: the skill makes workarounds ticket-bound and
time-boxed (30 days); without it, workarounds silently become permanent.

## E4 — fresh-consumer test
**Prompt**: "Write a test proving the Foundation `Modal` still opens with only the
documented props."
**Expected**: a fresh-consumer test that imports only the public package surface and renders
the component with documented props — never reaching into internals.
**Failure sign**: a test that imports the package source directly (a unit test in disguise).
**What the skill changes vs no skill**: the skill distinguishes a fresh-consumer test from a
unit test by the import path; a generic agent writes the latter and calls it a conformance
test.

## E5 — version bump under Freeze
**Prompt**: "Foundation v2.4.1 is out; should we bump?"
**Expected**: agent checks the Freeze notice in `docs/STATUS_ALL.md` and refuses to bump
without integrator approval recorded there.
**Failure sign**: agent bumps the version because "it's a patch".
**What the skill changes vs no skill**: the FREEZE rule in AGENTS.md is the constraint; the
skill makes the refusal explicit and names the artifact that would authorize the bump.

## E6 — bare ALLOWED marker is a stale escape hatch
**Prompt**: "My PR uses `data-ottili-workaround` to hide a layout bug."
**Expected**: agent requires a ticket reference (`FV2-WA: ISSUE-<digits>`) in the attribute or
the accompanying comment, with an owner and a date, or rejects the workaround.
**Failure sign**: agent accepts the workaround because "it ships".
**What the skill changes vs no skill**: the skill makes workarounds ticket-bound and
time-boxed (30 days); without it, workarounds silently become permanent.
**Exact command to verify**:
`python3 scripts/check_foundation_tokens.py --tokens <token.json> --require-ticket <file>`
must exit 0 for a ticketed marker and exit 1 with `raw colour #ff0000 not in token set` for a
bare `ALLOWED` marker. Without `--require-ticket` the bare marker is silently exempt, which is
the drift the skill exists to catch.
**Worked example good**: `<div style={{ color: '#ff0000' }} /* ALLOWED: FV2-WA: ISSUE-1234 owner: alice */ />`
**Worked example bad**: `<div style={{ color: '#ff0000' }} /* ALLOWED */ />` (no ticket — stale hatch).

## Verification checklist
- [ ] Every Foundation v2 import is a named import of a public export.
- [ ] No raw styling literals outside token-derived values.
- [ ] Every workaround carries `FV2-WA:` with owner + date (verified with `--require-ticket`).
- [ ] A fresh-consumer test exists and passes in isolation.
- [ ] Conformance report is committed or referenced.

## Near-miss prompts (act before the incident)
- **N1 — "The component works, who cares about the token."** Answer: no. A raw styling literal breaks the theme and the fresh-consumer test; replace it with the token.
- **N2 — "It's faster to import the inner module directly."** Answer: no. Deep imports bypass the public API and break when internals change; use the named public export.
- **N3 — "I'll add the workaround inline and clean it up later."** Answer: no. Every workaround must carry `FV2-WA:` with an owner and a date, or it is a permanent drift.
- **N4 — "The fresh-consumer test is just a unit test with a different name."** Answer: no. A unit test imports the package source; a fresh-consumer test imports the published package as a downstream consumer would.
- **N5 — "Foundation v2.4.1 is out, let's bump."** Answer: no. Check the Freeze notice in `docs/STATUS_ALL.md` and refuse without integrator approval.
- **N6 — "The ALLOWED marker has been there for months, it's fine."** Answer: no. Run with `--require-ticket`; a marker without `FV2-WA: ISSUE-<digits>` and `owner:` is a stale escape hatch, not a tracked workaround.
- **N7 — "The ticket is in the commit message, not the marker."** Answer: no. The marker must carry the ticket inline so the checker can exempt the line; a ticket in prose elsewhere is invisible to the check.
