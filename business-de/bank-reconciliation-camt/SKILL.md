---
name: bank-reconciliation-camt
description: "Parse CAMT.053/MT940 bank statements, match postings to open items with multi-key heuristics, detect duplicates and unallocated differences, and produce a reconciled Kontoauszug. Use when an agent must reconcile a bank account, auto-allocate payments to customers/suppliers, or flag unexplained differences. Not for card acquirer statements or non-SEPA currencies."
license: MIT-compat
compatibility: "framework-agnostic; ISO 20022 camt.053, SWIFT MT940, EBICS, offline"
metadata: {}
allowed-tools: []
---

# bank-reconciliation-camt

## When to use this skill

Use this skill when an agent must reconcile a bank account from a
**CAMT.053** (ISO 20022) or **MT940** (SWIFT) statement: parse the file,
match postings to open items (customers, suppliers, refunds), detect
duplicates and unallocated differences, and produce a reconciled statement.

Do **not** use it for card acquirer (card scheme) statements, non-SEPA
currencies, or cash-counting tasks.

## Procedure

1. **Parse the statement** — XML (camt.053) or MT940 (SWIFT plain text).
   Extract account, opening/closing balance, and every entry (amount, date,
   reference, counterparty, purpose).
2. **Verify balances** — opening balance + entries = closing balance. A
   mismatch is a hard stop.
3. **Match postings** — run the heuristic cascade in
   `references/procedures.md` §3 (amount → reference → counterparty → date).
4. **Flag duplicates** — same amount + same reference + same date = duplicate.
5. **Allocate** — assign each matched entry to an open item; write off the
   difference with a reason code.
6. **Verify** — run `scripts/recon_check.py`; the verification checklist.

## Decision tables

### Match priority

Match in this order; stop at the first rule that fires:

| Step | Signal | Wins when |
|---|---|---|
| 1 | amount exact + ledger reference | unambiguous |
| 2 | amount exact + counterparty name | reference missing or free text |
| 3 | amount within ±tolerance + date in window | partial match |
| 4 | reference only | allocation by mandate/SEPA ID |

Never allocate on amount alone when two open items share the amount. The
full cascade with worked examples is in `references/procedures.md` §3.

### Duplicate detection

| Signal | Threshold |
|---|---|
| Same amount | exact to cents |
| Same reference (Verwendungszweck) | exact |
| Same value date | same calendar day |
| All three true | **duplicate** — block allocation |

### Reason codes

| Code | Use when |
|---|---|
| ROUNDING | difference under EUR 0.01 |
| BANK_FEE | bank charge not in the ledger |
| FX | currency conversion delta |
| UNALLOCATED | entry with no open item, documented |

## Pitfalls from research

- camt.053 is mandatory in SEPA since 2014; MT940 has **no fixed
  deprecation date** for reporting messages (SWIFT, Nov 2025). Both remain in
  use; handle both.
- The current camt.053 message version is **camt.053.001.08**
  (namespace `urn:iso:std:iso:20022:tech:xsd:camt.053.001.08`). Files
  declaring `.008.01` are legacy drafts — re-parse with the `.001.08` schema
  rather than accepting the older namespace silently.
- MT940 purpose lines are free text and often truncated; camt.053 structures
  them in structured fields (Mandat-ID, EndToEndId). Prefer camt.053 for
  matching.
- A duplicate posting is **not** a rounding difference — block it and escalate
  to the bank.
- Unallocated differences under EUR 0.01 are rounding; above that they need a
  reason code. Accepted codes: ROUNDING, BANK_FEE, FX, UNALLOCATED.

## Verification checklist

- [ ] Statement parsed (camt.053 or MT940)
- [ ] Opening + entries = closing balance
- [ ] Every entry matched or explicitly unallocated
- [ ] Duplicates blocked, not silently allocated
- [ ] Differences under EUR 0.01 are rounding
- [ ] `scripts/recon_check.py` exits 0

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
