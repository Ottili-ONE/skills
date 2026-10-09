# Procedures — skr-journal-mapping

All versions are read from `config/versions.json`. Never hardcode a version in
this file or in scripts. The SKR account list is a stable standard; the
tax-key *rates* change with UStG amendments and are read from config.

## 1. Pin the Kontenrahmen

| Kontenrahmen | Entity | Default in config |
|---|---|---|
| SKR04 | GmbH | `skr-journal-mapping.kontenrahmen` |
| SKR03 | GmbH & Co. KG | alternative; pin explicitly |

The account list is stable; the tax keys are not. Re-verify against
DATEV/IDR before each build.

## 2. Map account to tax key

Read rates from `config/versions.json` -> `skr-journal-mapping.ust_rates_2026`:

| Rate | Law | Use |
|---|---|---|
| 19% | UStG §12 Abs. 1 | standard rate, domestic sales |
| 7% | UStG §12 Abs. 2 | reduced rate |
| 0% | UStG §4 Nr. 1, §6 | intra-EU, exports |

Every account has a *default* tax key; the transaction context can override it
(intra-EU customer => 0%). The override is a decision, not a silent fallback.

## 3. Generate a journal entry

A journal entry has five mandatory fields:

| Field | Meaning | Rule |
|---|---|---|
| Konto | account number | fits Sachkontenlaenge |
| Betrag | amount | comma decimal, EUR |
| Steuerschluessel | tax key | 19 / 07 / 00 |
| Belegdatum | voucher date | YYYYMMDD with leading zeros |
| Buchungsdatum | booking date | YYYYMMDD, >= Belegdatum |

Bad example (tax key guessed, not mapped):

```
Konto 4000, Betrag 1.200,00, Steuerschluessel 19   <- rate hardcoded
```

Good example (rate read from config, override documented):

```
Konto 4100, Betrag 1.200,00, Steuerschluessel 00, reason=intra-EU
```

## 4. Lock a period

A period lock is a technical enforcement with three parts:

1. Set the lock flag for the period (e.g. `2026-12`).
2. Record the approval (who, when, why).
3. Block further bookings until an override with documented evidence.

Never treat the lock as a policy statement — enforce it in code.

## 5. Reconcile

Compare generated journals against source invoices. A mismatch is a
**blocking error** until a human reviewer resolves it with documented evidence
of review. Common causes of a tax-key mismatch:

- reduced-rate item mapped to a standard-rate account
- wrong account mapping (SKR03 vs SKR04 overlap)
- wrong Steuerschluessel on the source invoice
- intra-EU transaction charged at 19%

## 6. Retain

Keep the journal and its source invoices for 8 years (vouchers) / 10 years
(books) per AO §147 Abs. 3 n.F. Record checksum and retrieval path.
