---
name: ust-edge-cases
description: "Apply German VAT edge cases correctly: reverse charge (§3g UStG, services only), Kleinunternehmer §19, intra-EU B2B (06/0), OSS/IOSS, rounding to cents, and the e-invoice interplay. Use when an agent must decide the tax treatment of a cross-border or small-business invoice, pick the right Steuerschlüssel, or avoid the reverse-charge trap. Not for domestic standard-rate B2C sales."
license: MIT-compat
compatibility: "framework-agnostic; German UStG, EU VAT rules, offline"
metadata: {}
allowed-tools: []
---

# ust-edge-cases

## When to use this skill

Use this skill when an agent must decide the VAT treatment of a German invoice
that is **not** a plain domestic 19%/7% B2C sale — i.e. cross-border supplies,
small-business invoicing, installment payments, cent-level rounding, or the
interaction with e-invoicing rules.

Do **not** use it for domestic standard-rate B2C sales (covered by
`skr-journal-mapping`), for non-EU third-country supplies, or for tax advice
beyond what the sources below support.

## Procedure

1. **Identify the edge case** — reverse charge, small business, intra-EU,
   OSS, rounding, or e-invoice interplay (see decision table).
2. **Apply the rule** — pick the Steuerschlüssel and the tax amount.
3. **Check the precondition** — reverse charge (§3g) needs both a valid
   customer USt-IdNr. **and** a supply of **services** (IT, consulting,
   construction). §3g covers services, not goods; a goods supply with a buyer
   USt-IdNr. uses the general intra-EU rule (§4a) at 0% without reverse charge.
   Kleinunternehmer requires the prior-year turnover ≤ EUR 20,000 (UStG §19
   Abs. 1, read from config). A USt-IdNr. alone is not enough to trigger
   reverse charge.
4. **Generate the journal** — use `skr-journal-mapping` for the accounts and
   `scripts/ust_check.py` for the arithmetic.
5. **Verify** — run `scripts/ust_check.py` and the verification checklist.

## Decision tables

All three tables below — edge-case selection, the goods-vs-services split,
and the e-invoice interplay — are expanded with worked examples and legal
sources in `references/procedures.md` §1-§6. The condensed rules:

Condensed rules: reverse charge (§3g) shifts the VAT debt to the buyer
for intra-community **services** only; a goods supply to a customer with a
USt-IdNr. is 0% under the general intra-EU rule (§4a) and is not reverse
charge. Kleinunternehmer (§19, turnover under EUR 20,000) charge no VAT and
issue a sonstige Rechnung; invoices under EUR 250 gross are exempt from the
issuing obligation. Worked examples and legal sources are in
`references/procedures.md` §1–§6.


## Pitfalls from research

The single trap that catches most agents: **reverse charge (§3g) is services
only** — a goods supply to a customer that supplies a USt-IdNr. is taxed at
0% under the general intra-EU rule (§4a), not reverse charge. The full list of
five traps, with sources, is in `references/procedures.md` §1–§6.


## Verification checklist

- [ ] Edge case identified per decision table
- [ ] Precondition checked (USt-IdNr., turnover threshold, services category)
- [ ] Tax key matches the legal rate
- [ ] Tax amount computed and rounded to cents
- [ ] `scripts/ust_check.py` exits 0
- [ ] E-invoice interplay documented (e-invoice vs sonstige Rechnung)

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
