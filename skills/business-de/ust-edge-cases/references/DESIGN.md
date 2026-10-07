# DESIGN: ust-edge-cases

## Trigger description (SKILL.md description draft, <=1024 chars)
"Handle German VAT edge cases for Ottili flows: reverse charge (Schuldnerschaft), small business (Kleinunternehmer), intra-EU triangulation, OSS/IOSS, rounding rules and the e-invoice interplay. Use when an agent must decide which VAT rule applies to a transaction, emit a compliant tax line, or reconcile a VAT return. Not for general VAT policy or non-German jurisdictions."

## Procedure outline
1. **Classify the transaction** — domestic, intra-EU, import/export, small business, or reverse-charge. The classification decides the tax key and the reporting box.
2. **Apply the small-business test** — UStG §19 Abs. 1: turnover under EUR 20,000 (previous year) => no VAT charged; if the agent is a Kleinunternehmer, never emit a VAT line for domestic sales.
3. **Reverse charge (Schuldnerschaft)** — UStG §3g: certain services (IT, consulting, construction) shift the VAT debt to the recipient; emit the tax key with the reverse-charge indicator and the buyer's USt-IdNr.
4. **Intra-EU / OSS** — EU sales use the USt-IdNr. validation (VIES) and the OSS (or IOSS for goods) reporting scheme; do not charge German VAT.
5. **Rounding** — German VAT rounds per commercial rule (EUR 0.5 up at the line level, then per tax key); never round the total before the tax split.
6. **E-invoice interplay** — a reverse-charge invoice must still be a valid e-invoice (§14 UStG) and carry the Schuldnerschaft indicator in BT-11.
7. **Reconcile** — compare the emitted tax lines against the UStJA/MEPHIT output; log any deviation.

## Scripts planned
- `scripts/ust_classify.py` — classifies a transaction and returns the tax key + rule applied.
- `scripts/ust_round.py` — applies the German VAT rounding rule per line and per tax key.
- `scripts/ust_reconcile.py` — compares journal tax lines with the UStJA export.

## Five eval prompts
1. "We are a Kleinunternehmer with EUR 15,000 turnover. Do we charge VAT on a domestic sale?" -> must say no, cite UStG §19, and emit no VAT line.
2. "A German buyer receives IT consulting from a French supplier. Who pays the VAT?" -> must say the buyer (Schuldnerschaft, UStG §3g) and require the buyer's USt-IdNr.
3. "Round EUR 100.005 for a 19% VAT line." -> must apply the commercial rounding rule and explain it.
4. "We sell digital services to EU consumers via OSS. What do we report?" -> must name OSS/IOSS and the USt-IdNr. requirement.
5. "A reverse-charge invoice is also an e-invoice. What extra field is needed?" -> must name the Schuldnerschaft indicator in BT-11 and the USt-IdNr. validation.

## What this skill does better than generic agents
- Encodes the Kleinunternehmer threshold as a test, not a footnote.
- Distinguishes reverse charge from the general intra-EU rule, which generic agents conflate.
- Treats rounding as a first-class step with the line-before-total rule.
