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
3. **Check the precondition** — reverse charge needs both a valid customer
   USt-IdNr. **and** a supply of goods (§13b covers goods, not services);
   Kleinunternehmer requires the prior-year turnover ≤ EUR 22,000 (2026).
   A USt-IdNr. alone is not enough to trigger reverse charge.
4. **Generate the journal** — use `skr-journal-mapping` for the accounts and
   `scripts/ust_check.py` for the arithmetic.
5. **Verify** — run `scripts/ust_check.py` and the verification checklist.

## Decision tables

All three tables below — edge-case selection, the goods-vs-services split,
and the e-invoice interplay — are expanded with worked examples and legal
sources in `references/procedures.md` §1-§6. The condensed rules:

Condensed rules: the reverse-charge regime (§13b) covers goods only — a
service sold to a customer that supplies a USt-IdNr. is still taxed by the
general place-of-performance rule. A small business under the
Kleinunternehmer rule charges no VAT on its sales and issues a "sonstige
Rechnung", but remains able to receive e-invoices. Invoices under EUR 250
gross are exempt from the issuing obligation. The full tables (edge-case selection, goods-vs-services split, e-invoice
interplay) with worked examples and legal sources are in
`references/procedures.md` §1-§6.

The full tables (edge-case selection, goods-vs-services split, e-invoice
interplay) with worked examples and legal sources are in
`references/procedures.md` §1-§6.

The full tables (edge-case selection, goods-vs-services split, e-invoice
interplay) with worked examples and legal sources are in
`references/procedures.md` §1-§6.

## Pitfalls from research

The single trap that catches most agents: **reverse charge (§13b) is goods
only** — a service sold to a customer that supplies a USt-IdNr. is still
taxed by the general place-of-performance rule. The full list of five traps,
with sources, is in `references/procedures.md` §1-§6.

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
