# EVALS — skr-journal-mapping

Each prompt lists the expected behaviour and the failure signs an agent must
watch for. Run the relevant script and compare the output to the expected.

## 1. Prompt
**Prompt:** "Map our SKR04 revenue account 4000 to a tax key."

**Expected behaviour:** Run `scripts/map_skr.py --account 4000 --skr 04`.
Expect `ok: true`, `default_tax_key: "19"`, `rate_percent: 19`, and
`rates_from_config` read from `config/versions.json` (never a hardcoded 19).
The agent must also state the caveat: intra-EU supplies on 4000 use 0%, and
the mapping must be re-verified against the current UStG before each build.

**Failure signs:** Reporting 19% without citing the config source; claiming the
rate is universal; not flagging the intra-EU override.

## 2. Prompt
**Prompt:** "Generate a journal entry for a domestic B2B sale, EUR 1,200.00
net, 19% VAT, on account 4000."

**Expected behaviour:** Run `scripts/generate_journal.py` with the line
`{"account":"4000","side":"S","amount":1200,"tax_key":"19","belegdatum":"20260601"}`.
Expect one entry with `konto: "4000"`, `steuerschluessel: "19"`,
`rate_percent: 19`. Then run `scripts/journal_check.py` on a complete journal
(sales leg + bank leg + tax account 1570); it must report `OK journal balanced`.

**Failure signs:** Emitting a dot decimal; writing the rate into the script
instead of reading config; producing an entry with no `steuerschluessel`;
reporting `ok: true` without running the balance check.

## 3. Prompt
**Prompt:** "Lock our December 2026 period."

**Expected behaviour:** Run `scripts/period_lock.py --period 2026-12 --action
lock --approver "Tax Advisor"`. Expect `ok: true, locked: true` and a state
file recording `locked_at`, `locked_by`, and `lock_reason`. A subsequent
`--action status` must show `locked: true`. A further `--action lock` must
report `already_locked: true` rather than silently re-locking.

**Failure signs:** Locking without an approver; treating the lock as a policy
statement instead of a technical flag; re-locking and losing the audit trail.

## 4. Prompt
**Prompt:** "Our journal says tax key 19% but the invoice says 7%. What do we
do?"

**Expected behaviour:** The agent must flag this as a **blocking mismatch** and
list the possible causes: a reduced-rate item mapped to a standard-rate
account; a wrong account mapping (SKR03 vs SKR04 overlap, e.g. 4000 vs 4100);
a wrong Steuerschluessel on the source invoice; or an intra-EU transaction
charged at 19%. The agent must require human review with documented evidence
before release — never silently pick a key.

**Failure signs:** Guessing the key; "fixing" the journal to match the invoice
without reviewing the account mapping; not recording the review evidence.

## 5. Prompt
**Prompt:** "Reconcile our generated journals against the source invoices."

**Expected behaviour:** Run `scripts/generate_journal.py` then
`scripts/journal_check.py`. The report must list matched lines, blocking
errors (unbalanced journal, tax key outside the valid set, account outside SKR
ranges, tax key present without a tax-account line), and the count of lines
that need human review. Every blocking error must be escalated, not written off.

**Failure signs:** Reporting `ok: true` while `journal_check.py` returns 2;
auto-writing-off mismatches; not recording the reconciliation run.

## 6. Prompt
**Prompt:** "Map account 4100 for an intra-EU sale."

**Expected behaviour:** Run `scripts/map_skr.py --account 4100 --skr 04
--intra-eu`. Expect `default_tax_key: "00"`, `rate_percent: 0`, and
`override: "already 0% (intra-EU/export) - no override needed"`. If the same
account were 4000 with `--intra-eu`, the override must flip the key to `00`
and say so explicitly.

**Failure signs:** Ignoring the `--intra-eu` flag; returning 19% for an
intra-EU supply; not recording the override reason in the output.

## 7. Prompt
**Prompt:** "Generate a journal from a line with tax key 99 on account 4000."

**Expected behaviour:** `scripts/generate_journal.py` must report
`ok: false`, `blocking: 1`, and list `tax_key must be 19/07/00, got '99'` in
`blocking_errors`. The output file must still be written so the error is
auditable.

**Failure signs:** Crashing instead of reporting; writing `ok: true` for an
invalid line.

## Near-miss triggers

### N1. "Account 4000 is always 19%"
**Trap:** account 4000 (Vertrieb) defaults to 19%, but an intra-EU supply
overrides it to 00. Run `scripts/map_skr.py --account 4000 --intra-eu` and
record the override reason. Verified 2026-10-09 against SKR 03/04.

### N2. "The journal balances, so it is correct"
**Trap:** a balanced journal can still carry a tax key outside the valid set
(19/07/00), an account outside SKR ranges, or a tax key without a
tax-account line. Run `scripts/journal_check.py` and escalate every blocking
error.

### N3. "Period lock is just a reminder"
**Trap:** a period lock is a hard control. `scripts/period_lock_check.py`
exits non-zero when a booking lands in a locked period. Wire it into the
fiscal close, not a warning.

### N4. "Tax key 99 is a valid special key"
**Trap:** the valid set is 19/07/00 (plus intra-EU 06/0, 09/0, 13/0 for
edge cases). `scripts/generate_journal.py` reports `ok: false` for 99 and
still writes the file so the error is auditable.
