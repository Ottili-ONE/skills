---
name: skr-journal-mapping
description: "Map the German chart of accounts (SKR03 / SKR04) to automatic journal entries with correct tax keys, period locks, and GoBD-compliant retention. Use when an agent must generate journal entries from invoices, assign Steuerschluessel (tax keys), lock a period for the tax return, or reconcile SKR03/SKR04 account mappings. Not for non-German GAAP, generic bookkeeping, or DATEV EXTF formatting (use datev-extf)."
license: MIT-compat
compatibility: "framework-agnostic; offline; reads config/versions.json"
metadata: {}
allowed-tools: []
---

# skr-journal-mapping

## When to use this skill

Use this skill when an agent must turn invoices or booking data into SKR-compliant
automatic journal entries, assign the right Steuerschluessel (tax key) per account,
lock a period for the tax return, or reconcile generated journals against source
documents. Do **not** use it for non-German GAAP, generic bookkeeping theory, or
DATEV EXTF CSV formatting (use `datev-extf` for that).

## Procedure

1. **Pin the Kontenrahmen** — SKR04 (GmbH) or SKR03 (GmbH & Co. KG). Read the
   default from `config/versions.json` (`skr-journal-mapping.kontenrahmen`) and
   never hardcode. The account list is stable; the tax keys are not.
2. **Map account to tax key** — every account carries a default Steuerschluessel:
   19% standard-rate revenue, 7% reduced-rate, 0% for intra-EU and exports. Read
   the rates from config (`ust_rates_2026`); a hard-coded 19% in a script is a
   bug. Re-verify against the current UStG before each build.
3. **Generate journal entries** — one entry per invoice line: Konto, Betrag,
   Steuerschluessel, Belegdatum, Buchungsdatum. Validate mandatory fields per SKR
   rules before writing.
4. **Lock the period** — at month-end / year-end, set the lock flag, record the
   approval, and prevent further bookings until an override with documented
   evidence. This is a technical enforcement, not a policy statement.
5. **Reconcile** — compare generated journals against source invoices. Report
   mismatches as blocking errors until a human reviewer resolves them with
   documented evidence of review.
6. **Retain** — keep the journal and its source invoices for 8 years (vouchers)
   / 10 years (books) per AO §147; record checksum and retrieval path.

## Decision tables

### Account-to-tax-key mapping (SKR04, default)

| Account | Meaning | Default tax key | When it changes |
|---|---|---|---|
| 4000 | Sales — domestic | 19% | intra-EU customer => 0% |
| 4100 | Sales — intra-EU | 0% | domestic customer => 19% |
| 4200 | Sales — exports (non-EU) | 0% | domestic customer => 19% |
| 4300 | Sales — reduced rate | 7% | standard-rate item => 19% |
| 8000 | Other income | 19% | exempt services => 0% |

The same accounts exist in SKR03 with different semantics; the skill refuses to
guess and pins the Kontenrahmen in config.

## Pitfalls from research

- **Tax-key drift**: the account-to-tax-key structure is stable but the *rate*
  changes with UStG amendments. Read rates from config; never hardcode.
- **SKR03 vs SKR04 overlap**: accounts 4000/4100 exist in both frameworks with
  different semantics. Pin the Kontenrahmen in config and refuse to guess.
- **AM-Konten**: Automatikkonten are posted automatically by DATEV; a BU-Schluessel
  other than "40" on them is rejected or double-counted.
- **Wrong tax keys produce wrong returns** — the highest-error-rate area in
  German VAT. Mismatches are blocking until human-reviewed.

## Verification checklist

- [ ] Kontenrahmen pinned from config
- [ ] Tax keys read from config, never hardcoded
- [ ] Every journal entry has Konto, Betrag, Steuerschluessel, Belegdatum, Buchungsdatum
- [ ] Period lock flag set with approval record
- [ ] Mismatches reported as blocking errors with human review evidence
- [ ] Retention period recorded (8y vouchers / 10y books) with checksum

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
