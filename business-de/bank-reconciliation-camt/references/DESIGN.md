# DESIGN — bank-reconciliation-camt

## Trigger description (draft for SKILL.md front matter)

> Use this skill when an Ottili agent must reconcile a bank account from a
> CAMT.053 (ISO 20022) or MT940 (SWIFT) statement — parse the file, assign
> each posting to an open item, spot duplicate bookings and unexplained
> differences, and produce a reconciled Kontoauszug. Triggers: "reconcile this
> camt.053", "allocate this payment to a customer", "is this booking a
> duplicate", "the balance does not match".

## What this skill does better than a generic agent

- **Balance equation is the first hard stop**: opening balance + entries =
  closing balance. A mismatch blocks everything downstream.
- **Match cascade, not a single heuristic**: amount+reference →
  amount+counterparty → amount±tolerance+date window → reference-only. Stop
  at the first that fires. Never allocate on amount alone when two open
  items share the amount.
- **Duplicate detection is explicit**: amount + reference + value date all
  matching an earlier entry → duplicate, block allocation, escalate to the
  bank. The near-miss is allocating two identical 100.00 entries to a 200.00
  open item and silently absorbing the duplicate.
- **Unallocated differences need a reason code** (UNALLOCATED, BANK_FEE, FX,
  Rounding), never a write-off to "other income".
- **MT940 structured fields win over the purpose line**: match on the `:61:`
  reference first; the `:86:` purpose line is supplementary.

## Procedure outline

1. **Parse the statement** — XML (camt.053) or MT940. Extract account,
   opening/closing balance, and every entry (amount, date, reference,
   counterparty, purpose).
2. **Verify balances** — opening + entries = closing. Mismatch = hard stop.
3. **Match postings** — run the cascade in `references/procedures.md` §3.
4. **Flag duplicates** — amount + reference + value date all matching an
   earlier entry.
5. **Allocate** — assign each matched entry to an open item; clear remaining
   differences with a reason code.
6. **Verify** — run `scripts/recon_check.py`.

## Decision tables

### Match priority

| Step | Signal | Wins when |
|---|---|---|
| 1 | amount exact + ledger reference | unambiguous |
| 2 | amount exact + counterparty name | reference missing or free text |
| 3 | amount within ±tolerance + date in window | partial match |
| 4 | reference only | allocation by mandate/SEPA ID |

### Reason codes

| Code | When |
|---|---|
| UNALLOCATED | no open item matched |
| BANK_FEE | bank charge with no invoice |
| FX | currency conversion difference |
| Rounding | under EUR 0.01 |

## Scripts planned

| Script | Purpose |
|---|---|
| `scripts/recon_check.py` | Validate a reconciliation JSON; exit non-zero on balance mismatch, duplicate, or matched-without-open-item. |

## Five eval prompts

1. **Valid reconciliation.** "Reconcile: opening 100.00, one entry +100.00,
   closing 200.00, matched." → exits 0, "OK reconciliation valid". Failure
   sign: exit 2 with "balance mismatch".
2. **Duplicate.** "Two entries both show EUR 100.00 with reference INV-001
   on 2026-10-09." → duplicate, block allocation, escalate. Failure sign:
   allocating both to a 200.00 open item.
3. **Unallocated.** "An entry of EUR 100.00 has no matching open item. Can
   I write it off to other income?" → no; require a reason code. With
   `matched: false, reason_code: "UNALLOCATED"` the check passes. Failure sign:
   marking it matched without an open item.
4. **Rounding.** "The difference is EUR 0.005." → under EUR 0.01 is rounding,
   allocate to "Rounding". Failure sign: creating a fake 0.01 entry.
5. **MT940 reference.** "MT940 with `:61:2610091000,100,D,,X,REF123` and
   `:86:001?00RECHNUNG123`. Which reference?" → match on the `:61:` reference
   (REF123) first; the `:86:` purpose line is supplementary. Failure sign:
   matching on the purpose line only.
