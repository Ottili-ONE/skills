# DESIGN — skr-journal-mapping

## Trigger description (draft for SKILL.md front matter)

> Use this skill when an Ottili agent must map German SKR03/SKR04 ledger
> accounts to journal entries and tax keys (19/7, 16/1, 19/0, 06/0, 09/0,
> 13/0), build automatic Buchungszeilen, or enforce a period lock before the
> fiscal close. Triggers: "map account 4000", "generate the journal for this
> invoice", "is this period locked", "which Steuerschlüssel for account 4100".

## What this skill does better than a generic agent

- **Account → tax-key defaults with an override rule**: account 4000
  (Vertrieb) defaults to 19%, but an intra-EU supply overrides it to 00. The
  skill records the override reason in the output instead of silently
  applying the default.
- **Valid tax-key set is explicit**: 19/07/00 for domestic, plus 06/0, 09/0,
  13/0 for intra-EU edge cases. A key outside this set is a blocking error,
  not a warning.
- **Journal balance is not enough**: `scripts/journal_check.py` also checks
  account ranges, tax-key validity, and the presence of a tax-account line
  for every taxed line.
- **Period lock is a hard control, not a reminder**: `scripts/period_lock.py`
  locks a period and `scripts/period_lock_check.py` exits non-zero when a
  booking lands in a locked period. Wire it into the fiscal close.
- **SKR 03 vs 04 is a first-class parameter**: the same account number means
  different things in the two charts; the skill takes `--skr 03|04` on every
  call.

## Procedure outline

1. **Identify the chart** — SKR 03 or SKR 04.
2. **Map the account** — look up the default tax key for the account; apply
   the intra-EU / export override if the flag is set.
3. **Build the journal line** — account, contra account, amount, tax key,
   tax-account line.
4. **Validate** — run `scripts/journal_check.py`; escalate every blocking
  error.
5. **Lock the period** — run `scripts/period_lock.py` before the close and
   `scripts/period_lock_check.py` after every booking batch.

## Scripts planned

| Script | Purpose |
|---|---|
| `scripts/map_skr.py` | Map an account to its default tax key; apply overrides. |
| `scripts/generate_journal.py` | Generate an automatic journal from invoice lines. |
| `scripts/journal_check.py` | Validate a journal; exit non-zero on blocking errors. |
| `scripts/period_lock.py` | Lock a fiscal period. |
| `scripts/period_lock_check.py` | Check no booking lands in a locked period. |

## Five eval prompts

1. **Account 4000 default.** "Map account 4000 for a domestic sale." → 19%.
   Failure sign: returning 0% or 7%.
2. **Intra-EU override.** "Map account 4000 for an intra-EU sale." → 00, with
   an explicit override reason. Failure sign: returning 19% and ignoring the
   flag.
3. **Invalid tax key.** "Generate a journal from a line with tax key 99."
   → `ok: false`, `blocking: 1`, `tax_key must be 19/07/00, got '99'`. Failure
   sign: crashing or writing `ok: true`.
4. **Unbalanced journal.** "Check a journal whose debits ≠ credits." →
   Blocking error. Failure sign: reporting `ok: true`.
5. **Period lock.** "A booking lands in a locked period." →
   `period_lock_check.py` exits non-zero. Failure sign: treating the lock as a
   reminder.
