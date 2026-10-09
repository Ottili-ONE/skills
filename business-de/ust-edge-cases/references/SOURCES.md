# ust-edge-cases — SOURCES

Retrieval date: 2026-10-09. Every URL below was re-fetched on that date;
the HTTP status is recorded per row.

| # | Source | URL | Retrieved | Verified version | Notes |
|---|---|---|---|---|---|
| 1 | IHK Chemnitz — E-Rechnung für inländische B2B-Umsätze | https://www.ihk.de/chemnitz/e-rechnung | 2026-10-09 | Nr. 5781150 | **200 OK (followed a 301 redirect)**. Confirms: Kleinunternehmerregelung (§19 Abs. 1 UStG) exempt from the e-invoicing obligation, §34a UStDV n.F., "über den 1. Januar 2028 weiterhin als sonstige Rechnungen", Kleinbetagsrechnungen (< 250 €) exempt, Empfangspflicht ab 2025. §13b not mentioned on this page — the reverse-charge-inside-the-obligation claim is not independently corroborated here. |
| 2 | IHK Rhein-Neckar — Umsatzsteuer | https://www.ihk.de/rhein-neckar/recht/steuerrecht/umsatzsteuer | 2026-10-09 | — | **200 OK**. Confirms "Seit Anfang 2025 sind elektronische Rechnungen für alle inländischen Unternehmen obligatorisch". Sub-page `/e-rechnungspflicht-5931752` (200 OK) confirms Kleinbetagsrechnungen (bis 250 Euro) and steuerfreie Umsätze are exempt and may still be "sonstige Rechnung". |
| 3 | steuer-berater.de — Umsatzsteuer lexikon | https://www.steuer-berater.de/lexikon/umsatzsteuer | 2026-10-09 | — | **200 OK**. Confirms §13b Reverse-Charge-Verfahren (goods, Steuerschuldumkehr) and the Kleinunternehmerregelung Vorjahresgrenze (§18 Abs. 2 UStG). |
| 4 | UStG (primary law) | https://www.gesetze-im-internet.de/ustg/ | 2026-10-09 | current | **404 at retrieval (re-confirmed)**. Tried `ustg`, `ustg/`, `UStG`, `ustg.html`, `ustg_2025-01-01.html`, `ustg_2024-01-01.html`, `ustg_2025-12-31.html`, plus titelsuche/volltextsuche — all 404. Mark as unverified; re-fetch before audit. |
| 5 | UStDV §23 (rounding) | https://www.gesetze-im-internet.de/ustdv/ | 2026-10-09 | current | **404 at retrieval (re-confirmed)**. Mark as unverified. |
| 6 | EU VIES (VAT Information Exchange System) | https://ec.europa.eu/taxation_customs/vies/ | 2026-10-09 | — | **200 OK**. Used to verify customer USt-IdNr. before applying 06/0. |
| 7 | R3_VERIFIED_FACTS.md | ../ottili-planning/inputs/R3_VERIFIED_FACTS.md | 2026-10-06 | — | starting point, re-verified 2026-10-09. |

**Re-verification note (2026-10-09):** the IHK pages (rows 1-2) are the
strongest sources this pass and now carry the Kleinunternehmer-exemption and
Kleinbetagsrechnung claims. The `gesetze-im-internet.de` law pages (rows 4-5)
remain 404 even though the host itself is up (BEG at `/beg/` returns 200) —
the site appears to have moved its law pages. The §13b reverse-charge claim
is corroborated by steuer-berater.de (row 3), not by the IHK Chemnitz page.

**Conflict note:** no conflicts among the 200-OK sources. The only open item
is the primary-law URLs.
