# SOURCES — gobd-archive

Retrieval date for every entry: 2026-10-08 (unless noted). Versions pinned in
`config/versions.json`; re-verify before relying on any version-sensitive fact.

| # | Source | URL | Verified version | Notes / conflicts |
|---|---|---|---|---|
| 1 | AO §147 Abs. 3 n.F. (Aufbewahrungspflichten) | https://dejure.org/gesetze/AO/147.html | effective 2025-01-01 | **CORRECTED 2026-10-08:** dejure.org/gesetze/AO/147.html returned 200 with the statute text (Bücher/Jahresabschluss 10 Jahre, Buchungsbelege 8 Jahre, Handels-/Geschäftsbriefe 6 Jahre). The canonical gesetze-im-internet.de/ao/ URL returned 404 at retrieval; the BEG URL now resolves to the *Bundesentschädigungsgesetz*, not the retention statute. Re-fetch before an audit. |
| 2 | steuer-berater.de GoBD lexikon | https://www.steuer-berater.de/lexikon/gobd | 200 (2026-10-08) | Confirms: 10y Bücher/Jahresabschlüsse, 8y Buchungsbelege, 6y andere Unterlagen/Geschäftsbriefe, all effective 01.01.2025. Also: Verfahrensdokumentation is mandatory; fines up to EUR 50,000 (§378 AO). |
| 3 | whk-controlling.de GoBD Archivierung Guide | https://www.whk-controlling.de/wissen/gobd-archivierung-guide | 200 (2026-10-08) | Confirms the 8/10/6 split and "vorher 10 Jahre" for vouchers. Includes a retention calculator. |
| 4 | provimedia.de Aufbewahrungsfristen 2025 | https://www.provimedia.de/blog/aufbewahrungsfristen | 200 (2026-10-08) | Independent corroboration: "Seit 2025: Belegate 8 Jahre, Bücher 10 Jahre, Geschäftsbriefe 6 Jahre (§ 147 AO)". datePublished 2026-07-11. |
| 5 | kostenlos-erechnung.de e-Rechnung Archivierung Pflicht | https://kostenlose-erechnung.de/ratgeber/e-rechnung-archivierung-pflicht/ | 2026-10-08 | Confirms 8y for Rechnungen, the original-XML-must-survive rule, and the BMF Schreiben 15.10.2025 Randziffer 60. |
| 6 | BMF Schreiben 2024-11-15 / 2025-10-15 | https://www.bmf.gv.at/ (search) | 2024-11-15, 2025-10-15 | Governs the BEG IV effective date, e-invoicing and GoBD. Re-verify annually. |
| 7 | GoBD 2014 (BMF Schreiben 14.11.2014, updated 11.03.2024) | https://www.bmf.gv.at/ (search) | 2014-11-14 / 2024-03-11 | Superseded principles retained for older retention periods. |
| 8 | BDO GoBD guidance | https://www.bdo.de/ | 2024 | Confirms immutability as a technical property (hash-chaining, append-only). |
| 9 | DATEV GoBD Leitfaden | https://www.datev.de/ | 2024 | Practical guidance; confirms the Verfahrensdokumentation checklist and export formats. |
| 10 | EU Directive 2014/55/EU | https://ec.europa.eu/digital-building-blocks/ | EN 16931 mandate | Parent directive; audit export formats may reference it. |

## Conflicts / version-sensitive notes

- **Source URL drift (CORRECTED 2026-10-08).** `gesetze-im-internet.de/ao/` returns
  404 and `.../beg/` now resolves to the Bundesentschädigungsgesetz. The retention
  classes are now pinned against `dejure.org/gesetze/AO/147.html` (200, statute text)
  plus provimedia.de and steuer-berater.de. Re-fetch the canonical URLs before any
  audit and let the tax advisor confirm.
- The "10 years for everything" rule is the older guidance; it applies only to
  vouchers whose retention period started before 2025. Always mark the effective
  date (2025-01-01) wherever it is cited.
- Verfahrensdokumentation is mandatory for the full retention period (per
  steuer-berater.de); a missing one is a fine risk, not a paperwork gap.
- Immutability is a technical property (append-only + hash-chaining), not a
  policy statement (per BDO guidance).
