# skr-journal-mapping — procedures and worked examples

Retrieval date: 2026-10-09. All version-sensitive facts are pinned in
`config/versions.json`; re-verify before relying on a fact.

## 1. Account set selection

| Entity type | Account set | Notes |
|---|---|---|
| GmbH, large | SKR04 | ~260 accounts, 1xxx assets, 2xxx liabilities, 4xxx income/expense, 8xxx equity/tax |
| GmbH, small | SKR03 | 93 accounts; 1xxx assets differ from SKR04 |
| Einzelunternehmen / GbR | SKR03 | common default |
| KG / large | SKR04 | |

SKR03 and SKR04 are **not** mixable. A journal that uses account 1200
(SKR03: Bank) and account 1570 (SKR04: USt) in the same file is invalid.

## 2. Line classification

1. Is the line an **asset** (1xxx)? — bank, receivables, equipment.
2. Is it a **liability** (2xxx)? — liabilities, tax accounts.
3. Is it **income/expense** (4xxx/5xxx)? — revenue, cost accounts.
4. Is it **tax/equity** (8xxx)? — USt accounts, retained earnings.

## 3. Tax keys (Steuerschlüssel)

| Key | Rate | Meaning | Source |
|---|---|---|---|
| 19 | 19% | Standard rate (domestic) | UStG §12 Abs. 1 |
| 7 | 7% | Reduced rate | UStG §12 Abs. 2 |
| 16/1 | 16%/1% | Legacy (pre-2020, old rate) | historical, do not use |
| 06/0 | 0% | Intra-EU supply (B2B), Steuerverrechnung | UStG §4a, MwStSimplification |
| 09/0 | 0% | Internal service / intercompany | DATEV Steuerkennzeichen |
| 13/0 | 19% split | Installment (Soll/IST) | UStG §13 Abs. 1 Nr. 1 Buchung |

**Pitfall:** key 16/1 must not be used for new postings. The 2020 rate cut
moved standard from 16% to 19% and reduced from 7% to 5%; any journal still
using 16/1 is a legacy artefact.

## 4. Automatic journal generation

For a domestic B2B sale of goods (19%):
```
S  1200  Bank              119.00  19
H   8000  Revenue           100.00  19
H   1570  USt                19.00  19
```
Sum debit = sum credit = 119.00. The tax line (1570 in SKR04, 1571 in SKR03)
carries the same tax key as the revenue line.

**Bad example** — tax line missing:
```
S  1200  Bank              119.00  19
H   8000  Revenue           100.00  19
```
This fails the USt-Anmeldung plausibility check: the tax account has no
amount, so the tax declaration and the journal disagree.

## 5. Period lock (Monatsschluss)

1. Close all postings for the period.
2. Set the Monatsschluss flag in the ledger.
3. Block further postings (per Buchungsstapel: no new Zeilen with that
   Mandant/Monat/Jahr).
4. Run `scripts/period_lock_check.py`.
5. Only then run the USt-Anmeldung for that period.

**Pitfall:** posting a corrective entry after the lock without an explicit
unlock + re-lock cycle breaks the plausibility check and the GoBD
"nachträgliche Änderungen" rule.

## 6. Verification

Run `scripts/journal_check.py <journal.json>` — exits 0 on balance and
valid tax keys, 2 otherwise.
