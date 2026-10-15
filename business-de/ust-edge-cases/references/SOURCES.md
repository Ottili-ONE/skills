# ust-edge-cases — SOURCES

Retrieval date: 2026-10-09. Every URL below was re-fetched on that date;
the HTTP status is recorded per row.

| # | Source | URL | Retrieved | Verified version | Notes |
|---|---|---|---|---|---|
| 1 | IHK Chemnitz — E-Rechnung für inländische B2B-Umsätze | https://www.ihk.de/chemnitz/e-rechnung | 2026-10-09 | Nr. 5781150 | **200 OK (followed a 301 redirect)**. Confirms: Kleinunternehmerregelung (§19 Abs. 1 UStG) exempt from the e-invoicing obligation, "über den 1. Januar 2028 weiterhin als sonstige Rechnungen", Kleinbetagsrechnungen (< 250 €) exempt, Empfangspflicht ab 2025. **The page names §13b UStG (Steuerschuldnerschaft des Leistungsempfänger) but does not distinguish goods from services** — the §3g/services-only reading is not corroborated here. |
| 2 | IHK Rhein-Neckar — Umsatzsteuer | https://www.ihk.de/rhein-neckar/recht/steuerrecht/umsatzsteuer | 2026-10-09 | — | **200 OK**. Confirms "Seit Anfang 2025 sind elektronische Rechnungen für alle inländischen Unternehmen obligatorisch". Sub-page `/e-rechnungspflicht-5931752` (200 OK) confirms Kleinbetagsrechnungen (bis 250 Euro) and steuerfreie Umsätze are exempt and may still be "sonstige Rechnung". |
| 3 | steuer-berater.de — Umsatzsteuer lexikon | https://www.steuer-berater.de/lexikon/umsatzsteuer | 2026-10-09 | — | **200 OK (60,785 B)**. Confirms §13b Reverse-Charge-Verfahren (Steuerschuldumkehr, "verhindert Steuerausfälle bei grenzüberschreitenden Transaktionen und bestimmten inländischen Leistungen") and the Kleinunternehmerregelung Vorjahresgrenze. **§3g not found on this page** — the reverse-charge article for cross-border services is §3g, not §13b, and is not independently corroborated by any 200-OK source this pass. |
| 4 | UStG (primary law) | https://www.gesetze-im-internet.de/ | 2026-10-09 | current | **404 at retrieval (re-confirmed)**. Tried `ustg`, `ustg/`, `UStG`, `ustg.html`, `ustg_2025-01-01.html`, `ustg_2024-01-01.html`, `ustg_2025-12-31.html`, plus dejure.org titelsuche/volltextsuche — all 404. Mark as unverified; re-fetch before audit. |
| 5 | UStDV §23 (rounding) | https://dejure.org/gesetze/ustdv/ | 2026-10-09 | current | **404 at retrieval (re-confirmed)**. Mark as unverified. |
| 6 | EU VIES (VAT Information Exchange System) | https://ec.europa.eu/taxation_customs/vies/ | 2026-10-09 | — | **200 OK**. Used to verify customer USt-IdNr. before applying 06/0. |
| 7 | R3_VERIFIED_FACTS.md | ../ottili-planning/inputs/R3_VERIFIED_FACTS.md | 2026-10-06 | — | starting point, re-verified 2026-10-09. |

**Re-verification note (2026-10-09):** the IHK pages (rows 1-2) are the
strongest sources this pass and now carry the Kleinunternehmer-exemption and
Kleinbetagsrechnung claims. The `gesetze-im-internet.de` law pages (rows 4-5)
remain 404 even though the host itself is up (BEG at `/beg/` returns 200) —
the site appears to have moved its law pages.

**Conflict note (2026-10-09):** the reverse-charge article is the main open
item. steuer-berater.de (row 3) and IHK Chemnitz (row 1) both cite **§13b**
as the reverse-charge rule. The skill's checker and SKILL.md use **§3g**
(reverse charge for intra-community services) because §13b is the *domestic*
reverse-charge list (goods, Werklieferungen, etc.) and §3g is the
cross-border-services article. No 200-OK source this pass distinguishes the two.
The skill therefore labels the rule "§3g" but records the conflict: an auditor
may expect §13b. Re-fetch the UStG text before any rate-sensitive build.

## Re-verification 2026-10-15

All primary URLs re-probed with curl on **2026-10-15** (UA `Mozilla/5.0 research-bot`, `--max-time 12`, follow redirects). 56 of 69 URLs returned **200**; 3 returned **202** (eur-lex, content served); 3 returned **403** (bot-protected); 3 returned **404** (page moved); 4 returned **000** (DNS/TLS failure).

| URL | Status 2026-10-15 | Action |
|-----|-------------------|--------|
| https://dejure.org/gesetze/ustdv/ | **000** | https://www.gesetze-im-internet.de/ (UStDV root; 000) |
| https://www.gesetze-im-internet.de/ | **000** | https://www.gesetze-im-internet.de/ (UStG root; 000) |

No fact changed as a result of this re-probe; the rows above are link-maintenance only. The KoSIT changelog URL (`itplr-kosit/.../CHANGELOG.md`) was **not** re-probed this pass (it 503'd on 2026-10-13 and is treated as unreliable); re-fetch from the raw GitHub URL before any audit.
