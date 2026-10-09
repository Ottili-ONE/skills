---
name: skr-journal-mapping
description: "Map German SKR03/SKR04 ledger accounts to journal entries, tax keys (19/7, 16/1, 19/0, 06/0, 09/0, 13/0) and automatic Buchungszeilen; build and validate period-lock and closing-concept rules. Use when an agent must classify an invoice line, decide the correct SKR account + Steuerschlüssel, generate an automatic journal, or enforce a period lock before the fiscal close. Not for US GAAP, IFRS consolidation or non-German VAT."
license: MIT-compat
compatibility: "framework-agnostic; German SKR03/SKR04, DATEV Buchungsstapel, offline"
metadata: {}
allowed-tools: []
---

# skr-journal-mapping

## When to use this skill

Use this skill when an agent must map a German invoice line to an SKR03 or SKR04
ledger account, pick the correct Steuerschlüssel (tax key), generate an automatic
journal (Buchungszeile) or enforce a period lock before the fiscal close.

Do **not** use it for US GAAP, IFRS consolidation, non-German VAT, or
balance-sheet preparation (that is a separate skill).

## Procedure

1. **Pick the account set** — SKR03 (small, 93 accounts) or SKR04 (large,
   ~260 accounts). Default to SKR04 unless the entity runs SKR03.
2. **Classify the line** — asset / liability / income / expense / tax / equity
   per the table in `references/procedures.md` §2.
3. **Assign the tax key** — pick from the set {19, 7, 16/1, 06/0, 09/0,
   13/0} according to the rate and the supply type. Never guess a key, since
   it feeds the USt-Anmeldung directly.
4. **Generate the journal** — debit/credit side, account, tax key, amount,
   reference. Validate with `scripts/journal_check.py`.
5. **Lock the period** — set the Monatsschluss flag, block further postings,
   run `scripts/period_lock_check.py`, then close.

## Decision tables

### Tax key selection

| Scenario | Tax key | Umsatzsteuersatz |
|---|---|---|
| Standard rate domestic | 19 | 19% |
| Reduced rate domestic | 7 | 7% |
| Standard rate (old) | 16/1 | 16% / 1% |
| Intra-EU supply (B2B) | 06/0 | 0% (Steuerverrechnung) |
| Internal service | 09/0 | 0% |
| Installment (Soll/IST) | 13/0 | 19% split |

The worked examples and the legal sources for each key are in
`references/procedures.md` §3.

## Pitfalls from research

- SKR03 and SKR04 share the 4xxx income/expense range and parts of the 2xxx
  liability range, but the 1xxx asset range differs between the two sets, so
  a journal that mixes accounts from both sets is invalid.
- The tax key **16/1** is legacy (pre-2020); do not use it for new postings.
- A journal that carries a taxed key but leaves the tax account
  (1570/1571/1572) without an amount fails the USt-Anmeldung plausibility
  check — the declaration and the ledger would disagree.

## Verification checklist

- [ ] Account set chosen (SKR03 or SKR04)
- [ ] Line classified per decision table
- [ ] Tax key matches the legal rate
- [ ] Journal balances (sum debit = sum credit)
- [ ] Period lock applied before close
- [ ] `scripts/journal_check.py` exits 0

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
