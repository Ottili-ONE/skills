# DESIGN: bank-reconciliation-camt

## Trigger description (SKILL.md description draft, <=1024 chars)
"Parse and reconcile German bank statements in CAMT.053/MT940 format for Ottili flows: statement parsing, matching heuristics, duplicate detection and transaction allocation. Use when an agent must ingest a bank statement, match it against ledger entries, detect duplicates, or allocate an unmatched transaction. Not for general accounting logic or non-ISO-20022 formats."

## Procedure outline
1. **Identify the format** — CAMT.053 (ISO 20022, XML) or MT940 (SWIFT, structured text). The parser differs; never mix them.
2. **Parse the statement** — extract account, opening/closing balances, statement date, and transactions (amount, value date, reference, counterparty).
3. **Detect duplicates** — same amount + value date + reference => duplicate; reject the second with a reason.
4. **Match transactions** — match by amount first, then by reference (End-to-End-ID/Kundenreferenz), then by value date within a tolerance window.
5. **Allocate unmatched** — hold unmatched transactions in a staging queue with the reason; never auto-write-off.
6. **Reconcile balances** — compare the parsed closing balance with the ledger's bank account balance; on mismatch, stop and report.
7. **Log** — record the run, the matched/unmatched counts and the reconciliation report.

## Scripts planned
- `scripts/parse_camt.py` — parses a CAMT.053 XML statement into a machine-readable JSON.
- `scripts/parse_mt940.py` — parses an MT940 statement into the same JSON schema.
- `scripts/reconcile.py` — runs the matching heuristics and emits a reconciliation report.

## Five eval prompts
1. "Parse this CAMT.053 XML and report the closing balance." -> must extract the balance and the transaction count.
2. "Two statements have the same amount, value date and reference. Are they duplicates?" -> must say yes and reject the second.
3. "Match this statement against our ledger." -> must report matched/unmatched counts and the tolerance window used.
4. "A transaction has no reference. How do we allocate it?" -> must stage it with a reason, never auto-write-off.
5. "The parsed closing balance does not match the ledger. What do we do?" -> must stop and report the delta.

## What this skill does better than generic agents
- Distinguishes CAMT.053 from MT940 with a parser per format instead of guessing.
- Encodes the duplicate detection rule (amount + value date + reference) explicitly.
- Treats unmatched transactions as a staging queue, not a silent write-off.
