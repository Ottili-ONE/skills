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

1. **Pick the account set** — SKR03 (small, 93 accounts, standard for
   Kleinunternehmen / small GmbH) or SKR04 (large, ~260 accounts, standard for
   larger GmbHs). Default to SKR04 unless the entity is known to run SKR03.
2. **Classify the line** — asset / liability / income / expense / tax / equity
   using the decision table in `references/procedures.md` §2.
3. **Assign the tax key** — 19 (19% USt), 7 (7% USt), 16/1 (16% USt),
   06/0 (Erwerb innergemeinschaftlich), 09/0 (Sonderposten/interne
   Leistungen), 13/0 (Soll/IST bei Dauerleistungen). Never guess: the key
   drives the USt-Anmeldung.
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

## Pitfalls from research

- SKR03 and SKR04 share account numbers 4xxx (income) and some 2xxx (liabilities)
  but differ in the 1xxx (assets) range; a mixed SKR03/SKR04 journal is invalid.
- The tax key **16/1** is legacy (pre-2020); do not use it for new postings.
- A journal with a tax key but no amount on the tax account (account 1570/1571
  in SKR04) fails the USt-Anmeldung plausibility check.

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
