# bank-reconciliation-camt — procedures and worked examples

Retrieval date: 2026-10-09. Version-sensitive facts are pinned in
`config/versions.json`; re-verify before relying on a fact.

## 1. Format selection

| Format | Standard | Use when |
|---|---|---|
| camt.053 | ISO 20022, XML | bank provides it (SEPA default since 2014) |
| MT940 | SWIFT MT, plain text | legacy bank or EBICS FIN channel |

camt.053 is preferred: structured fields (Mandat-ID, EndToEndId,
BIC/IBAN of counterparty) make matching far more reliable than MT940's
free-text Verwendungszweck lines.

## 2. Parse

**camt.053** — XML with namespace `urn:iso:std:iso:20022:tech:xsd:camt.053.008.01`:
- `/Document/BkToCstmrStmt/Stmt/Ntry[]` — entries
- each entry: `NtryId`, `BookgDt`/`ValDt`, `Amt` (credit/debit), `NtryDtl[]`
- counterparty: `RltdPties/Cdtr`/`Dbtr`, `RltdPties/Agt`
- references: `Refs/EndToEndId`, `Refs/MndtRltdInf/MndtId`

**MT940** — plain text, SWIFT:
- `:20:` — transaction reference number
- `:21:` — related message reference
- `:25:` — account identification
- `:28C:` — statement number
- `:60F:` — opening balance
- `:61:` — booking line (`YYMMDD`, credit/debit, amount, `C`/`D`, `M`/`S`, `X`, ref)
- `:86:` — purpose lines (up to 4 lines, often truncated)

## 3. Matching cascade

1. **Amount exact + reference in ledger** — unambiguous, allocate.
2. **Amount exact + counterparty name** — reference missing or free text.
3. **Amount ± tolerance + date within window** (default 3 days) — partial.
4. **Reference-only** — allocation by mandate/SEPA mandate ID.

Never allocate on amount alone when two open items share the amount.

## 4. Duplicate detection

A posting is a duplicate when **all three** hold:
- same amount (to cents)
- same reference
- same value date

Block and escalate to the bank; do not allocate.

## 5. Differences

| Difference | Action |
|---|---|
| < EUR 0.01 | rounding, allocate to "Rounding" |
| ≥ EUR 0.01 | reason code required (BANK_FEE, FX, UNALLOCATED) |

## 6. Worked examples

**Good camt.053 allocation** — entry amount 100.00, EndToEndId `ABC123`,
open item `INV-001` for exactly 100.00 → matched, difference 0.00.

**Bad** — allocating two 100.00 entries to one 200.00 open item without
checking references. If one entry is a duplicate, the reconciliation
balances but the duplicate is silently absorbed.

**Bad MT940** — `:61:2610091000,100,D,,X,REF123` followed by
`:86:001?00RECHNUNG123` — the reference in `:61:` (REF123) and the purpose
line (RECHNUNG123) are different fields; match on the `:61:` reference first.

## 7. Verification

Run `scripts/recon_check.py <recon.json>` — exits 0 on a valid
reconciliation, 2 otherwise.
