# EVALS — skr-journal-mapping

Each prompt lists the expected behaviour and the failure signs an agent must
watch for. Run the relevant script and compare the output to the expected.

## 1. Prompt
**Prompt:** "Map our SKR04 revenue account 4000 to a tax key."

**Expected behaviour:** Run `python3 scripts/map_skr.py --account 4000 --skr 04`.
Expect `ok: true`, `default_tax_key: "19"`, `rate_percent: 19`, and `rates_from_config` read from `config/versions.json` (never a hardcoded 19).
The agent must also state the caveat: intra-EU supplies on 4000 use 0%, and
the mapping must be re-verified against the current UStG before each build.

**Failure signs:** Reporting 19% without citing the config source; claiming the
rate is universal; not flagging the intra-EU override.

## 2. Prompt
**Prompt:** "Generate a journal entry for a domestic B2B sale, EUR 1,200.00
net, 19% VAT, on account 4000."

**Expected behaviour:** Run `python3 scripts/generate_journal.py --skr 04 --lines `[{"account":"4000","side":"S","amount":1200,"tax_key":"19","belegdatum":"20260601"}]`--output /tmp/journal.json`. Expect one entry with `konto: "4000"`, `steuerschluessel: "19"`, `rate_percent: 19`. A single sales line does not
balance — the generator emits the sales leg only; the balance check must run
on a *complete* journal (sales leg + bank leg 1100 + tax account 1570). `python3 scripts/journal_check.py --journal /tmp/journal.json` on the bare
sales leg exits 2 with "journal does not balance"; on the complete journal
it reports `OK journal balanced`.

**Failure signs:** Emitting a dot decimal; writing the rate into the script
instead of reading config; producing an entry with no `steuerschluessel`;
reporting `ok: true` without running the balance check.

## 3. Prompt
**Prompt:** "Lock our December 2026 period."

**Expected behaviour:** Run `scripts/period_lock.py --period 2026-12 --action lock --approver "Tax Advisor"`. Expect `ok: true, locked: true` and a state
file recording `locked_at`, `locked_by`, and `lock_reason`. A subsequent `--action status` must show `locked: true`. A further `--action lock` must
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

**Expected behaviour:** Run `python3 scripts/generate_journal.py --skr 04 --lines `[...]` --output /tmp/journal.json` then python3 scripts/journal_check.py`--journal /tmp/journal.json. The report must list matched lines, blocking
errors (unbalanced journal, tax key outside the valid set, account outside SKR
ranges, tax key present without a tax-account line), and the count of lines
that need human review. Every blocking error must be escalated, not written
off. A complete journal (sales + bank + 1570) exits 0; an unbalanced one exits 2.

**Failure signs:** Reporting `ok: true` while `journal_check.py` returns 2;
auto-writing-off mismatches; not recording the reconciliation run.

## 6. Prompt
**Prompt:** "Map account 4100 for an intra-EU sale."

**Expected behaviour:** Run `scripts/map_skr.py --account 4100 --skr 04 --intra-eu`. Expect `default_tax_key: "00"`, `rate_percent: 0`, and `override: "already 0% (intra-EU/export) - no override needed"`. If the same
account were 4000 with `--intra-eu`, the override must flip the key to `00`
and say so explicitly.

**Failure signs:** Ignoring the `--intra-eu` flag; returning 19% for an
intra-EU supply; not recording the override reason in the output.

## 7. Prompt
**Prompt:** "Generate a journal from a line with tax key 99 on account 4000."

**Expected behaviour:** `python3 scripts/generate_journal.py --skr 04 --lines `[{"account":"4000","side":"S","amount":1200,"tax_key":"99","belegdatum":"20260601"}]`--output /tmp/j.json` must report `ok: false`, `blocking: 1`, and list `tax_key must be 19/07/00, got '99'` in `blocking_errors`. The output file
must still be written so the error is auditable.

**Failure signs:** Crashing instead of reporting; writing `ok: true` for an
invalid line.

## Near-miss triggers

Prompts that look fine at first glance but hide a trap. The agent must catch
the trap and still produce a passing artefact.

### N1. "Map account 4000, it is always 19%"
**Trap:** the tax key depends on the transaction, not the account. An
intra-EU supply on 4000 flips the key to `00` via the `--intra-eu` flag.
Ignoring the flag is a silent wrong journal.

### N2. "Lock the period, it is done"
**Trap:** locking is idempotent but not reversible. A double lock or a lock
of an already-posted period must be reported, not silently overwritten. `scripts/period_lock_check.py` exits non-zero on both.

### N3. "The journal balances, so the tax key is fine"
**Trap:** a balanced journal can still carry the wrong tax key. The checker
validates the key against the account's allowed set independently of the
balance. A balanced journal with key `99` on 4000 is a blocking error.

### N4. "SKR 03 and SKR 04 share the same accounts"
**Trap:** the account ranges differ between the charts (e.g. 4100 intra-EU
exists in both but 4200 is SKR 04 only). Always pass `--skr 03` or `--skr 04`; the default is a failure sign.

### N5. "Reconcile means the numbers add up"
**Trap:** reconciliation also means the tax key on the journal matches the
key on the source invoice and the period is locked. A journal that balances
but carries key `19` where the invoice says `07` is a mismatch.


---

## Run these checks

Every prompt above names a script and an expected exit code. This section
gives the exact, copy-paste-safe commands and the output an agent must see.
All commands are run from the skill directory
(`cd skills/business-de/skr-journal-mapping`). A single sales line does not
balance — the generator emits the sales leg only; the balance check must run
on a *complete* journal (sales leg + bank leg 1100 + tax account 1570).

```bash
# 2. generate a sales leg -> exit 0
python3 scripts/generate_journal.py --skr 04 --lines "$(cat evals_fixtures/sales_leg.json)" --output /tmp/journal.json
# {"ok": true, "entries": 1, "blocking": 0}

# 2b. balance check on the bare sales leg -> exit 2
python3 scripts/journal_check.py --journal /tmp/journal.json
# FAIL journal does not balance: debit=1200.00 credit=0.00

# 6. map 4100 intra-EU -> exit 0
python3 scripts/map_skr.py --account 4100 --skr 04 --intra-eu
# {"default_tax_key": "00", "rate_percent": 0,
#  "override": "already 0% (intra-EU/export) - no override needed"}

# 6b. map 4000 intra-EU -> exit 0, override flips the key
python3 scripts/map_skr.py --account 4000 --skr 04 --intra-eu
# {"default_tax_key": "00", "rate_percent": 0, "override": "..."}

# 7. invalid tax key 99 -> exits 1 then 2, file still written
python3 scripts/generate_journal.py --skr 04 --lines "$(cat evals_fixtures/bad_key.json)" --output /tmp/j.json
# {"ok": false, "entries": 0, "blocking": 1}
python3 scripts/journal_check.py --journal /tmp/j.json  # exits 2
# FAIL journal is empty -- a close needs at least one posting line

# 3. lock December 2026 -> exit 0
python3 scripts/period_lock.py --period 2026-12 --action lock --approver "Tax Advisor"
# {"ok": true, "locked": true}
python3 scripts/period_lock.py --period 2026-12 --action status
# {"locked": true}
python3 scripts/period_lock.py --period 2026-12 --action lock --approver "Tax Advisor"
# {"already_locked": true}
```

The tax key depends on the **transaction**, not the account (near-miss N1):
`map_skr.py --account 4000 --skr 04 --intra-eu` flips the key to `00`. A
balanced journal can still carry the wrong tax key (N3) — the checker
validates the key against the account's allowed set independently of the
balance. Verified 2026-10-14 against `config/versions.json` (SKR04 default,
UST rates 19/7/0 for 2026).
