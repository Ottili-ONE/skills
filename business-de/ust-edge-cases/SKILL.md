---
name: ust-edge-cases
description: "Apply German VAT edge cases correctly: reverse charge (§13b UStG) for goods only, Kleinunternehmer §19, intra-EU B2B (06/0), OSS/IOSS, rounding to cents, and the e-invoice interplay. Use when an agent must decide the tax treatment of a cross-border or small-business invoice, pick the right Steuerschlüssel, or avoid the reverse-charge trap. Not for domestic standard-rate B2C sales."
license: MIT-compat
compatibility: "framework-agnostic; German UStG, EU VAT rules, offline"
metadata: {}
allowed-tools: []
---

# ust-edge-cases

## When to use this skill

Use this skill when an agent must decide the VAT treatment of a German invoice
that is **not** a plain domestic 19%/7% B2C sale: reverse charge, small
business (Kleinunternehmer), intra-EU B2B, OSS/IOSS, rounding, or the
interaction with e-invoicing.

Do **not** use it for domestic standard-rate B2C sales (covered by
`skr-journal-mapping`), for non-EU third-country supplies, or for tax advice
beyond what the sources below support.

## Procedure

1. **Identify the edge case** — reverse charge, small business, intra-EU,
   OSS, rounding, or e-invoice interplay (see decision table).
2. **Apply the rule** — pick the Steuerschlüssel and the tax amount.
3. **Check the precondition** — reverse charge requires the customer's
   USt-IdNr. **and** that the supply is of goods (§13b is goods only);
   Kleinunternehmer requires the prior-year turnover ≤ EUR 22,000 (2026).
4. **Generate the journal** — use `skr-journal-mapping` for the accounts and
   `scripts/ust_check.py` for the arithmetic.
5. **Verify** — run `scripts/ust_check.py` and the verification checklist.

## Decision tables

### Edge case selection

| Scenario | Tax key | Tax amount | Precondition |
|---|---|---|---|
| Domestic standard | 19 | 19% of net | none |
| Domestic reduced | 7 | 7% of net | none |
| Reverse charge (§13b) — **goods** | 06/0 (or V091) | 0% | buyer USt-IdNr. valid, goods in §13b list |
| Intra-EU B2B supply | 06/0 | 0% | buyer USt-IdNr. valid, goods leave DE |
| Kleinunternehmer §19 | none (0) | 0% on sales | prior-year turnover ≤ EUR 22,000 |
| OSS (EU-wide) | V091 | 0% in DE, declared in home state | home state OSS registration |
| Rounding | — | 2 decimals (cents) | per §23 UStDV |

### Reverse charge — goods vs services

| Supply | §13b applies | Tax key |
|---|---|---|
| Goods (resale/processing), intra-EU | **yes** | 06/0 |
| Services (IT, consultancy, construction) | **no** | general place-of-performance rule (often 19) |

A valid USt-IdNr. is **necessary but not sufficient** for reverse charge.

### E-invoice interplay

| Invoice type | Issuing obligation | Document |
|---|---|---|
| Standard B2B | mandatory | e-invoice (EN 16931) |
| Reverse charge (§13b) | mandatory | e-invoice with tax amount 0.00, key 06/0 |
| Kleinunternehmer §19 | exempt | "sonstige Rechnung" (but must still **receive** e-invoices) |
| Kleinbetagsrechnung (< EUR 250 gross) | exempt | "sonstige Rechnung" |

## Pitfalls from research

- Reverse charge for **services** is not §13b; it is §13b only for **goods**
  (resale of goods). Services use the general place-of-performance rule.
- Kleinunternehmer cannot reclaim input VAT and must not issue an e-invoice
  with a tax line; their invoices are "sonstige Rechnung" (§19 UStG).
- OSS requires the home-state registration; a German business using OSS must
  still file the USt-Anmeldung for domestic sales.
- Rounding: per §23 UStDV, tax amounts are rounded to cents (2 decimals);
  half-up is the convention, but the tax authority accepts banker's rounding in
  practice — record the convention.
- A 0% tax key (06/0, 09/0, V091, 0) must not carry a tax amount; a
  reverse-charge line with a non-zero tax amount is a filing error.

## Verification checklist

- [ ] Edge case identified per decision table
- [ ] Precondition checked (USt-IdNr., turnover threshold, goods category)
- [ ] Tax key matches the legal rate
- [ ] Tax amount computed and rounded to cents
- [ ] `scripts/ust_check.py` exits 0
- [ ] E-invoice interplay documented (e-invoice vs sonstige Rechnung)

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
