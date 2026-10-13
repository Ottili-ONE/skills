# DESIGN — ust-edge-cases

## Trigger description (draft for SKILL.md front matter)

> Use this skill when an Ottili agent must decide the VAT treatment of a
> German invoice that is **not** a plain domestic 19%/7% B2C sale —
> cross-border supplies, small-business invoicing, installment payments,
> cent-level rounding, or the interaction with e-invoicing rules. Triggers:
> "reverse charge or 0%", "is this a Kleinunternehmer", "round this tax
> amount", "is a EUR 199.90 invoice an e-invoice".

## What this skill does better than a generic agent

- **The single trap that catches most agents**: reverse charge (§3g) is
  **services only**. A goods supply to a customer with a USt-IdNr. is 0% under
  the general intra-EU rule (§4a) and must **not** be labelled reverse charge.
  Verified 2026-10-09 against UStG §3g / §4a via dejure.org.
- **Reverse charge needs both preconditions**: a valid customer USt-IdNr.
  **and** a supply of services. A USt-IdNr. alone is not enough.
- **Kleinunternehmer is a turnover test** (prior year ≤ EUR 20,000, UStG §19
  Abs. 1), not a registration test. It charges no VAT and issues a sonstige
  Rechnung.
- **German tax rounding is half-up to cents**, not banker's rounding. Net
  EUR 33.33 at 19% → 6.3326 → 6.33.
- **Kleinbetagsrechnung (< EUR 250 gross)** is exempt from the issuing
  obligation but the business must still be able to *receive* e-invoices.

## Procedure outline

1. **Identify the edge case** — reverse charge, small business, intra-EU,
   OSS, rounding, or e-invoice interplay.
2. **Apply the rule** — pick the Steuerschlüssel and the tax amount.
3. **Check the precondition** — reverse charge needs both a valid customer
   USt-IdNr. **and** a supply of **services**. Kleinunternehmer needs prior-year
   turnover ≤ EUR 20,000.
4. **Generate the journal** — use `skr-journal-mapping` for the accounts and
   `scripts/ust_check.py` for the arithmetic.
5. **Verify** — run `scripts/ust_check.py` and the verification checklist.

## Decision tables

### Edge-case selection

| Scenario | Tax key | Amount | Note |
|---|---|---|---|
| domestic B2B 19% | 19 | net × 1.19 | standard |
| domestic B2B 7% | 07 | net × 1.07 | reduced |
| intra-EU goods B2B | 06/0 | 0.00 | §4a, not reverse charge |
| intra-EU services B2B | 06/0 | 0.00 | §3g reverse charge |
| Kleinunternehmer | 0 | 0.00 | §19 |
| OSS (import) | 06/0 | 0.00 | One Stop Shop |

## Scripts planned

| Script | Purpose |
|---|---|
| `scripts/ust_check.py` | Decide the VAT treatment for an invoice line; exits 0 on a valid decision. |

## Five eval prompts

1. **Intra-EU goods.** "Supply goods to a French customer with USt-IdNr.
   DE999999999. Net EUR 100." → 06/0, 0.00, no tax line. This is §4a, not
   reverse charge. Failure sign: 19%; labelling it reverse charge.
2. **Kleinunternehmer.** "EUR 18,000 turnover last year. Invoice a domestic
   customer for EUR 100." → no tax line, gross EUR 100 in revenue, tax key 0.
   Failure sign: a 19% tax line.
3. **Reverse charge on goods.** "Reverse charge on a supply of goods to a
   German customer." → Not §3g — §3g is services only. Failure sign: applying
   06/0 and calling it reverse charge.
4. **Rounding.** "Net EUR 33.33 at 19%." → 6.3326 → 6.33 (half-up). Failure
   sign: unrounded amount; banker's rounding.
5. **Kleinbetagsrechnung.** "This invoice is EUR 199.90 gross. Is it an
   e-invoice?" → Kleinbetagsrechnung (< EUR 250), exempt from the issuing
   obligation; a sonstige Rechnung is acceptable, but the business must still
   be able to receive e-invoices. Failure sign: treating it as a mandatory
   e-invoice.
