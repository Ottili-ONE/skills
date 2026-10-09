# bank-reconciliation-camt — EVALS

Eight realistic prompts with expected behaviour and failure signs. Each
names a concrete input, the correct output, and the near-miss that a strong
generic agent would most likely produce.

## 1. Prompt
> "Reconcile this camt.053: opening 100.00, one entry +100.00,
> closing 200.00, matched."

**Expected behaviour:** `scripts/recon_check.py` exits 0, "OK reconciliation valid".

**Failure signs:** exit 2 with "balance mismatch" — the balance equation is
the first hard stop.

## 2. Prompt
> "Two entries both show EUR 100.00 with reference INV-001 on
> 2026-10-09. What now?"

**Expected behaviour:** **duplicate** — block allocation, escalate to the
bank. `scripts/recon_check.py` exits 2 with "duplicate".

**Failure signs:** allocating both to a 200.00 open item; the
reconciliation balances but the duplicate is absorbed.

## 3. Prompt
> "An entry of EUR 100.00 has no matching open item. Can I just
> write it off to 'other income'?"

**Expected behaviour:** no — require a reason code (UNALLOCATED, BANK_FEE,
FX). With `matched: false, reason_code: "UNALLOCATED"` the check passes.

**Failure signs:** marking it matched without an open item; no reason code.

## 4. Prompt
> "The difference is EUR 0.005. Is that rounding?"

**Expected behaviour:** yes — under EUR 0.01 is rounding, allocate to
"Rounding". The check tolerates it in the balance equation.

**Failure signs:** treating 0.005 as a missing entry; creating a fake
0.01 entry to force the balance.

## 5. Prompt
> "The bank sent an MT940 with `:61:2610091000,100,D,,X,REF123` and
> `:86:001?00RECHNUNG123`. Which reference do I match on?"

**Expected behaviour:** match on the `:61:` reference (REF123) first; the
`:86:` purpose line is supplementary. If the ledger has RECHNUNG123 and the
bank has REF123, prefer the structured `:61:` field and fall back to
counterparty name.

**Failure signs:** matching on the purpose line only and failing to find
the open item; or matching on amount alone when two items share it.

## 6. Prompt (near-miss — matched without an open item)
> "Reconcile: opening 0.00, one entry +100.00, closing 100.00, and the
> entry is `matched: true`."

**Expected behaviour:** **rejected** — `matched: true` without an
`open_item_id` is not an allocation. `recon_check.py` exits 2.

**Failure signs:** calling a self-declared "matched" entry reconciled.

## 7. Prompt (near-miss — unallocated total above tolerance)
> "Opening 0.00, one entry +0.02, closing 0.02, entry not matched and no
> reason code. Is the reconciliation valid?"

**Expected behaviour:** **rejected** — the unallocated total (0.02) is at or
above the EUR 0.01 boundary and no reason code is declared. Add
`reason_code: "BANK_FEE"` (or FX / UNALLOCATED) and it passes.

**Failure signs:** treating a 0.02 gap as rounding because it is "small".

## 8. Prompt (near-miss — camt.053 namespace drift)
> "Parse this camt.053 file. Its root declares
> `urn:iso:std:iso:20022:tech:xsd:camt.053.008.01`."

**Expected behaviour:** the skill must flag `.008.01` as a **legacy draft**
namespace. The current version is `camt.053.001.08` (verified 2026-10-09
against the de.wikipedia Camt-Format article). Re-parse with the `.001.08`
schema; do not silently accept the older namespace.

**Failure signs:** parsing `.008.01` without noting the version drift.

## 9. Prompt (near-miss — reason code "matched" without an open item)
> "The entry has no open item, so we set `reason_code: "MATCHED"`."

**Expected behaviour:** **rejected** — `MATCHED` is not a valid reason code; the
valid set is `UNALLOCATED`, `BANK_FEE`, `FX`, `ROUNDING`. A matched entry must
carry an `open_item_id`. `recon_check.py` exits 2.

**Failure signs:** inventing a reason code to make the check pass.

## 10. Prompt (near-miss — duplicate window heuristic)
> "Two entries, EUR 100.00, 2026-10-09 and 2026-10-13, same reference.
> Is that a duplicate?"

**Expected behaviour:** **no** — the strict rule (amount + value_date + reference)
says different value dates, so they are distinct. The 5-day window heuristic is
disabled by default; only enable it deliberately with a recorded decision.

**Failure signs:** auto-enabling the 5-day window and blocking the second entry.

## 11. Prompt (near-miss — IBAN check-digit algorithm)
> "Reconcile this camt.053. The statement IBAN is
> `DE91 3704 0044 0532 0130 00`."

**Expected behaviour:** the skill must run the **Bundesbank Pruefzahlenberechnung**
(country-specific), not generic mod-97. `recon_check.py` exits 2 with
"IBAN invalid" — the spaces and the wrong algorithm both break it.

**Failure signs:** validating the IBAN with a library that only does mod-97.

## 12. Prompt (near-miss — MT940 line encoding)
> "Here is an MT940 extract: `D20040510D01,N021NONREF//...`. Is it usable?"

**Expected behaviour:** **yes, after decoding** — `D` = debit, `N` = not
reconciled, `021` = transaction code. The skill must decode the SWIFT field
codes before matching, never match on the raw string.

**Failure signs:** matching the raw `D01` against a camt.053 amount.
