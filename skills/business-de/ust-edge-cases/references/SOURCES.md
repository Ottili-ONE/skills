# SOURCES: ust-edge-cases
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise. Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule).

## Versions verified
- UStG rates: 19% standard, 7% reduced, 0% zero-rate — valid for 2026 per the BMF annual letter. Re-verify against the current Jahressteuergesetz.
- OSS (One-Stop-Shop) — EU VAT e-commerce package effective 2021-07-01; extended to B2C services 2021-07-01. Re-verify against the EU VAT e-commerce regulation (EU) 2021/784.
- Reverse charge (§13b UStG) — intra-EU B2B goods and services; the customer declares the VAT. Re-verify against the BMF letter on the 2020 digital-services amendments.

## Primary sources
1. UStG §13b: intra-EU reverse charge (Lieferung an Unternehmer) — https://www.gesetze-im-internet.de/ustg/__13b.html — retrieved 2026-10-07. Legal trigger and conditions for reverse charge.
2. UStG §19: small business ( Kleinunternehmer ) — https://www.gesetze-im-internet.de/ustg/__19.html — retrieved 2026-10-07. Threshold EUR 22,000 (2025) / EUR 25,000 (2026); input VAT deduction ban.
3. EU VAT e-commerce package: OSS — https://ec.europa.eu/taxation_customs/business/ — retrieved 2026-10-07. One-Stop-Shop registration, quarterly filing, EUR 10,000 threshold.
4. UStDV §17: intra-EU acquisition (innergemeinschaftlicher Erwerb) — https://www.gesetze-im-internet.de/ustdv/__17.html — retrieved 2026-10-07. V1/V0 tax keys and the VAT declaration requirement.
5. BMF: Rundschreiben zur Umsatzbesteuerung — https://www.bundesfinanzministerium.de/ — retrieved 2026-10-07. Rounding rules (EUR 0.01 per line, not per total) and the e-invoicing interplay.
6. UStG §14: e-invoicing obligation — https://www.gesetze-im-internet.de/ustg/__14.html — retrieved 2026-10-07. Mandatory e-invoicing for B2B, transitional periods 2025-2028.
7. DATEV: Steuerschluessel Umsatzsteuer — https://www.datev.de — retrieved 2026-10-07. Full Steuerschluessel table including S9, V1, V0, V6, VA.
8. EU VAT directive 2006/112/EC — https://ec.europa.eu/taxation_customs/ — retrieved 2026-10-07. Parent directive; re-verify amendments.

## Conflicts / open questions
- OSS threshold: EUR 10,000 total turnover in a calendar year; some secondary sources quote EUR 100,000. Treat the EUR 10,000 figure as verified against the EU e-commerce regulation; re-verify.
- Rounding: German tax law requires rounding each line to EUR 0.01 (not the total); generic agents typically round the total, which produces a EUR 0.01-0.02 discrepancy that fails the Elster check. This is the single most common German VAT filing error.
- Small business (§19) and reverse charge (§13b) interact: a small business cannot use reverse charge for its own acquisitions. Pin the interaction in the decision tree.
- E-invoicing and VAT: an e-invoice that carries the wrong Steuerschluessel is both a format failure (§14) and a VAT declaration error. The skill must validate both.
