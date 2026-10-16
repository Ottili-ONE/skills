# Merge decision — skr-journal-mapping into datev-extf

Recorded 2026-10-16 by SKL-W1-02. This file is a decision record, not an implementation
(the merge itself is a cross-job request, see `docs/gaps/SKL-W1-02.md` X-001).

## Why datev-extf and not ust-edge-cases

The canonical `skills/business-de/skr-journal-mapping/SKILL.md` already names
`[datev-extf](../datev-extf/)` under "Related skills" — the journal mapper emits the
Buchungsstapel (journal export) that the DATEV EXTF skill consumes. The USt skill only
*validates* the tax keys the mapper assigns; it does not consume the journal artefact.
So the natural merge target is `datev-extf`.

## What the merge would carry

From `skills/business-de/skr-journal-mapping/`:

- `SKILL.md` — SKR03/SKR04 account selection, tax-key table, period-lock states,
  retention periods (AO §147 Abs. 3 n.F., effective 2025-01-01).
- `references/procedures.md` §1–§6 — worked examples and legal sources.
- `scripts/journal_check.py`, `scripts/period_lock_check.py` — the two gates the
  SKILL.md "Verification checklist" requires.
- `tests/` — self-tests for both gates.

## Status

**NOT MERGED.** The canonical `skr-journal-mapping/` is owned by skills-business-de-r3
(`docs/R3_OWNERS.json`), so this job cannot move it. Recorded here so the next pass does
not re-derive the decision.
