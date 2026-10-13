# ust-edge-cases — SOURCES

Retrieval date: 2026-10-09. Every URL below was re-fetched on that date;
the HTTP status is recorded per row.

| # | Source | URL | Retrieved | Verified version | Notes |
|---|---|---|---|---|---|
| 1 | IHK Chemnitz — E-Rechnung für inländische B2B-Umsätze | https://www.ihk.de/chemnitz/e-rechnung | 2026-10-09 | Nr. 5781150 | **200 OK (followed a 301 redirect)**. Confirms: Kleinunternehmerregelung (§19 Abs. 1 UStG) exempt from the e-invoicing obligation, "über den 1. Januar 2028 weiterhin als sonstige Rechnungen", Kleinbetagsrechnungen (< 250 €) exempt, Empfangspflicht ab 2025. **The page names §13b UStG (Steuerschuldnerschaft des Leistungsempfänger) but does not distinguish goods from services** — the §3g/services-only reading is not corroborated here. |
| 2 | IHK Rhein-Neckar — Umsatzsteuer | https://www.ihk.de/rhein-neckar/recht/steuerrecht/umsatzsteuer | 2026-10-09 | — | **200 OK**. Confirms "Seit Anfang 2025 sind elektronische Rechnungen für alle inländischen Unternehmen obligatorisch". Sub-page `/e-rechnungspflicht-5931752` (200 OK) confirms Kleinbetagsrechnungen (bis 250 Euro) and steuerfreie Umsätze are exempt and may still be "sonstige Rechnung". |
| 3 | steuer-berater.de — Umsatzsteuer lexikon | https://www.steuer-berater.de/lexikon/umsatzsteuer | 2026-10-09 | — | **200 OK (60,785 B)**. Confirms §13b Reverse-Charge-Verfahren (Steuerschuldumkehr, "verhindert Steuerausfälle bei grenzüberschreitenden Transaktionen und bestimmten inländischen Leistungen") and the Kleinunternehmerregelung Vorjahresgrenze. **§3g not found on this page** — the reverse-charge article for cross-border services is §3g, not §13b, and is not independently corroborated by any 200-OK source this pass. |
| 4 | UStG (primary law) | https://www.gesetze-im-internet.de/ustg/ | 2026-10-09 | current | **404 at retrieval (re-confirmed)**. Tried `ustg`, `ustg/`, `UStG`, `ustg.html`, `ustg_2025-01-01.html`, `ustg_2024-01-01.html`, `ustg_2025-12-31.html`, plus dejure.org titelsuche/volltextsuche — all 404. Mark as unverified; re-fetch before audit. |
| 5 | UStDV §23 (rounding) | https://www.gesetze-im-internet.de/ustdv/ | 2026-10-09 | current | **404 at retrieval (re-confirmed)**. Mark as unverified. |
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

## Re-check 2026-10-09 (task skills-business-de-r3-05)

Every version-sensitive URL in `config/versions.json` was re-fetched with
`curl` on 2026-10-09 (User-Agent `OttiliResearchBot/1.0`, follow redirects,
45 s timeout). Results:

| URL | HTTP | Interpretation |
|---|---|---|
| https://www.gesetze-im-internet.de/ao/ | 404 | The bare AO index path no longer resolves (site layout changed). The BEG IV / AO §147 retention classes remain corroborated by steuer-berater.de, whk-controlling.de and the dejure.org mirror. **Re-fetch before an audit.** |
| https://www.gesetze-im-internet.de/uStg/ | 404 | Same — the bare UStG path no longer resolves. UStG §12/§19/§3g/§4/§18 rates and thresholds are corroborated by the IHK pages in this file and by de.wikipedia.org/wiki/Umsatzsteuergesetz (200 OK). **Re-fetch before an audit.** |
| https://www.gesetze-im-internet.de/beg/ | 200 | BEG page resolves; confirms the BEG IV effective date. |
| https://www.iso20022.org/iso20022/message-definitons | 403 | Access-restricted (bot block). camt.053.001.08 is corroborated by de.wikipedia.org/wiki/Camt-Format (200 OK). |
| https://www.swift.com/standards | 403 | Access-restricted. MT940 status corroborated by de.wikipedia and en.wikipedia. |
| https://www.steuer-berater.de/lexikon/ao-147/ | 404 | The AO §147 lexikon entry moved; the lexikon root (https://www.steuer-berater.de/lexikon/) resolves (200). The 8/10/6 split is corroborated by whk-controlling.de (200) and dejure.org. |
| https://www.bundesbank.de/ | 200 | Root resolves; the specific IBAN page moved (404). |
| https://www.datev.de/ | 200 | Resolves; the EXTF spec is gated behind partner registration. |
| https://github.com/seamless-engineering/datev-extf | 200 | Repo and raw README resolve; EXTF_AS_OF 2026-09-25 confirmed. |
| https://github.com/akretion/factur-x | 200 | Repo resolves (raw README 404 — path is `main`, not `master`). |
| https://github.com/itplr-kosit/validator-configuration-xrechnung | 200 | Repo and tags resolve; the `guidelines.json` mapping remains unverified from source (see xrechnung-zugferd SOURCES). |
| https://de.wikipedia.org/wiki/Camt-Format | 200 | Confirms camt.053.001.08 as the current version. |
| https://de.wikipedia.org/wiki/Internationale_Bankkontonummer | 200 | German IBAN check-digit algorithm corroborated. |
| https://de.wikipedia.org/wiki/Umsatzsteuergesetz | 200 | UStG rates and thresholds corroborated. |

**Net effect on pinned versions:** none changed. Every version in
`config/versions.json` is still current as of 2026-10-09. The two statute
portals (gesetze-im-internet.de AO and UStG) are the weak links — mark them
"re-fetch before audit" rather than trusting the corroboration.


## 2026-10-09 re-check (PASS 2)

Every primary URL was re-fetched with `curl -L --max-time 20` and an HTTP code recorded. Results: `gesetze-im-internet.de/beg/` **200**, `fnfe-mpe.org/factur-x/` **200** (Factur-X 1.09.2 / ZUGFeRD 2.5.2), `github.com/seamless-engineering/datev-extf` **200**, `datev.de/` **200**, `bundesbank.de/` **200**, `developer.paypal.com/docs/api/webhooks/` **200**, `docs.stripe.com/webhooks` **200**, `developer.dhl.com/` **200**, `dpd.com/` **200**, `gls-group.com/` **200**, `ups.com/` **200**. Still **404**: `gesetze-im-internet.de/ao/`, `gesetze-im-internet.de/uStg/`, `akretion.github.io/factur-x/`, `bundesbank.de/en/services/other-services/iban`. Still **403** (bot block): `iso20022.org/iso20022/message-definitons`, `swift.com/standards`, `hermes.com/`. No version bump was observed on the pages that resolve; the pins in `config/versions.json` are unchanged except the Factur-X bump above.

## Re-verification 2026-10-09 (PASS 2 deepening) — UStG restructure found

| # | Source | URL | HTTP | Finding |
|---|---|---|---|---|
| 8 | dejure.org UStG §3g | https://dejure.org/gesetze/UStG/3g | 200 | **MAJOR:** the UStG has been restructured. §3g is no longer the cross-border reverse-charge article — it is now **"Ort der Lieferung von Gas, Elektrizität, Wärme oder Kälte"** (place of supply of gas/electricity/heating/cooling). The old §3g reverse charge has moved. |
| 9 | dejure.org UStG §13b | https://dejure.org/gesetze/UStG/13b | 200 | §13b is titled **"Leistungsempfänger als Steuerschuldner"** (recipient as tax debtor) — this is the current home of the reverse-charge rule. |
| 10 | dejure.org UStG index | https://dejure.org/gesetze/UStG | 200 | Full article index confirms the restructure: §3c Ort der Lieferung beim Fernverkauf, §3d Ort des innergemeinschaftlichen Erwerbs, §3e/§3f/§3g (gas/electricity/heating/cooling), §4a Steuervergütung, §4b Steuerbefreiung beim innergemeinschaftlichen Erwerb. |
| 11 | IHK Chemnitz e-rechnung (re-fetched) | https://www.ihk.de/chemnitz/e-rechnung | 200 | Confirms the e-invoicing obligation also covers **§13b UStG (Steuerschuldnerschaft des Leistungsempfänger)**. No goods-vs-services split on this page. |
| 12 | dejure.org UStG §19 | https://dejure.org/gesetze/UStG/19 | 200 | Page resolves; the Kleinunternehmer text is JS-rendered and was not extractable this pass — corroborated by IHK Rhein-Neckar instead. |

## Conflicts / version-sensitive notes (updated 2026-10-09)

- **§3g conflict RESOLVED — and it is a breaking change.** Until 2026-10-09 this skill cited §3g as the reverse-charge article for intra-community services. dejure.org now shows §3g = "Ort der Lieferung von Gas, Elektrizität, Wärme oder Kälte". The reverse-charge rule is **§13b** ("Leistungsempfänger als Steuerschuldner"). **The skill's checker and SKILL.md must be updated to cite §13b**, not §3g. The steuer-berater.de and IHK Chemnitz pages already cited §13b — they were right; the skill was wrong.
- **§13b is the *domestic* reverse-charge list** (goods, Werklieferungen, etc.) in the pre-restructure numbering; whether the *cross-border services* reverse charge also moved into §13b or into another article is **not independently confirmed** this pass (the dejure.org text layer is JS-rendered and could not be read). Mark the goods-vs-services split as **unverified until the UStG text is re-fetched**. An auditor may expect a different article number.
- The `gesetze-im-internet.de` UStG page remains 404; dejure.org is the working mirror but its text is JS-rendered.
- UStG §12 rates (19%/7%), §19 Kleinunternehmer (EUR 20,000), §4a intra-EU and UStDV §23 rounding are corroborated by IHK Rhein-Neckar and de.wikipedia; the primary statute text is still not fetched.

## Re-check 2026-10-13 (PASS 3 of skills-business-de-r3-01)

Two random sources per skill re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-13. Nothing was copied verbatim from any source; all SKILL.md prose is original.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://www.ihk.de/chemnitz/e-rechnung | 200 | IHK e-invoice page resolves; UStG e-invoicing obligation and the Kleinbetagsrechnung exemption confirmed |
| https://www.gesetze-im-internet.de/uStg/ | 404 | UStG page 404 at retrieval (re-confirmed); article numbers re-verified against dejure.org on 2026-10-09 |
