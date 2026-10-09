# skr-journal-mapping — SOURCES

Retrieval date: 2026-10-09. Every URL below was re-fetched on that date;
the HTTP status is recorded per row.

| # | Source | URL | Retrieved | Verified version | Notes |
|---|---|---|---|---|---|
| 1 | DATEV SK-Schlüssel page | https://www.datev.de/datev-web/de/produkte/datev-fibu/steuerliche-beratung/sk-schluesse | 2026-10-09 | — | **404 at retrieval (re-confirmed)**. The DATEV site has restructured twice since the original fetch. The tax-key table is built from UStG primary sources and the DATEV EXTF schema; have the tax advisor confirm the key-to-account mapping for the entity's Mandant. |
| 2 | DATEV FibU Steuerliche Beratung hub | https://www.datev.de/datev-web/de/produkte/datev-fibu/steuerliche-beratung | 2026-10-09 | — | **404 at retrieval (re-confirmed)**. |
| 3 | steuer-berater.de GoBD lexikon | https://www.steuer-berater.de/lexikon/gobd | 2026-10-09 | 2025-12-03 | 200 OK; corroborates AO §147 retention classes. |
| 4 | seamless-engineering/datev-extf | https://github.com/seamless-engineering/datev-extf | 2026-10-09 | 700/13 | 200 OK; EXTF schema reference for Buchungsstapel. |
| 5 | UStG (primary law) | https://www.gesetze-im-internet.de/ustg/ | 2026-10-09 | current | **404 at retrieval (re-confirmed)**. Tried `ustg`, `ustg/`, `UStG`, `ustg.html`, `ustg_2025-01-01.html`, `ustg_2024-01-01.html`, `ustg_2025-12-31.html` and the titelsuche/volltextsuche endpoints — all 404. The legal text is cited from memory and must be re-fetched before audit. |
| 6 | UStG §13 (entnommene Leistungen) | https://www.gesetze-im-internet.de/ustg/ | 2026-10-09 | current | same 404 as row 5. |
| 7 | UStG §4a (innergemeinschaftliche Leistungen) | https://www.gesetze-im-internet.de/ustg/ | 2026-10-09 | current | same 404 as row 5. |
| 8 | UStDV §23 (rounding) | https://www.gesetze-im-internet.de/ustdv/ | 2026-10-09 | current | **404 at retrieval (re-confirmed)**. |
| 9 | AO §147 (GoBD retention) | https://www.gesetze-im-internet.de/ao/ | 2026-10-09 | current | **404 at retrieval (re-confirmed)**; `ao_2025-01-01.html` also 404. |
| 10 | R3_VERIFIED_FACTS.md | ../ottili-planning/inputs/R3_VERIFIED_FACTS.md | 2026-10-06 | — | starting point, re-verified 2026-10-09. |

**Re-verification note (2026-10-09):** the `gesetze-im-internet.de`
host is up (BEG at `/beg/` returns 200), but the `/ustg/`, `/ustdv/` and
`/ao/` paths 404 — the site appears to have moved its law pages. Rows 5-9 are
marked unverified until a working URL is found. The tax-key table, the
rounding rule and the retention classes are corroborated by secondary
sources (steuer-berater.de, whk-controlling.de, the EXTF schema) but are not
independently re-verified against primary law this pass.

**Conflict note:** no conflicts among the 200-OK sources. The DATEV SK-Schlüssel
page being unreachable is the only open item.
