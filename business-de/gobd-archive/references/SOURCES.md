# SOURCES — gobd-archive

Retrieval date for every entry: 2026-10-08 (unless noted). Versions pinned in
`config/versions.json`; re-verify before relying on any version-sensitive fact.

| # | Source | URL | Verified version | Notes / conflicts |
|---|---|---|---|---|
| 1 | AO §147 Abs. 3 n.F. (Aufbewahrungspflichten) | https://www.gesetze-im-internet.de/ao/ | effective 2025-01-01 | **Retrieval note:** the AO index page 404'd at 2026-10-08 (site layout changed). The classes are corroborated by steuer-berater.de and whk-controlling.de. Re-fetch before an audit. |
| 2 | steuer-berater.de GoBD lexikon | https://www.steuer-berater.de/lexikon/gobd | modified 2025-12-03 | Confirms: 10y Bücher/Jahresabschlüsse, 8y Buchungsbelege, 6y andere Unterlagen/Geschäftsbriefe, all effective 01.01.2025. Also: Verfahrensdokumentation is mandatory; fines up to EUR 50,000 (§378 AO). |
| 3 | whk-controlling.de GoBD Archivierung Guide | https://www.whk-controlling.de/wissen/gobd-archivierung-guide | modified 2026-04-14 | Confirms the 8/10/6 split and "vorher 10 Jahre" for vouchers. Includes a retention calculator. |
| 4 | kostenlos-erechnung.de e-Rechnung Archivierung Pflicht | https://kostenlose-erechnung.de/ratgeber/e-rechnung-archivierung-pflicht/ | 2026-10-08 | Confirms 8y for Rechnungen, the original-XML-must-survive rule, and the BMF Schreiben 15.10.2025 Randziffer 60. |
| 5 | BMF Schreiben 2024-11-15 / 2025-10-15 | https://www.bmf.gv.at/ (search) | 2024-11-15, 2025-10-15 | Governs the BEG IV effective date, e-invoicing and GoBD. Re-verify annually. |
| 6 | GoBD 2014 (BMF Schreiben 14.11.2014, updated 11.03.2024) | https://www.bmf.gv.at/ (search) | 2014-11-14 / 2024-03-11 | Superseded principles retained for older retention periods. |
| 7 | BDO GoBD guidance | https://www.bdo.de/ | 2024 | Confirms immutability as a technical property (hash-chaining, append-only). |
| 8 | DATEV GoBD Leitfaden | https://www.datev.de/ | 2024 | Practical guidance; confirms the Verfahrensdokumentation checklist and export formats. |
| 9 | R3_VERIFIED_FACTS.md (Ottili planning) | ../ottili-planning/inputs/R3_VERIFIED_FACTS.md | 2026-10-06 | Internal corroboration; lists the same 8/10/6 split and the "some pages contradict" caveat. |
| 10 | EU Directive 2014/55/EU | https://ec.europa.eu/digital-building-blocks/ | EN 16931 mandate | Parent directive; audit export formats may reference it. |

## Conflicts / version-sensitive notes

- The retention classes are **verified** (10y books/annual accounts, 8y
  vouchers, 6y commercial correspondence, all effective 2025-01-01) against
  steuer-berater.de and whk-controlling.de. The statute text itself could not
  be fetched (404) — re-fetch before an audit and let the tax advisor confirm.
- The "10 years for everything" rule is the older guidance; it applies only to
  vouchers whose retention period started before 2025. Always mark the effective
  date (2025-01-01) wherever it is cited.
- Verfahrensdokumentation is mandatory for the full retention period (per
  steuer-berater.de); a missing one is a fine risk, not a paperwork gap.
- Immutability is a technical property (append-only + hash-chaining), not a
  policy statement (per BDO guidance).
