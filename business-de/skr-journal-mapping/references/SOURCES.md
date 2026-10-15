# skr-journal-mapping — SOURCES

Retrieval date: 2026-10-09. Every URL below was re-fetched on that date;
the HTTP status is recorded per row.

| # | Source | URL | Retrieved | Verified version | Notes |
|---|---|---|---|---|---|
| 1 | DATEV SK-Schlüssel page | https://www.datev.de//sk-schluesse | 2026-10-09 | — | **404 at retrieval (re-confirmed)**. The DATEV site has restructured twice since the original fetch. The tax-key table is built from UStG primary sources and the DATEV EXTF schema; have the tax advisor confirm the key-to-account mapping for the entity's Mandant. |
| 2 | DATEV FibU Steuerliche Beratung hub | https://www.datev.de/ | 2026-10-09 | — | **404 at retrieval (re-confirmed)**. |
| 3 | steuer-berater.de GoBD lexikon | https://www.steuer-berater.de/lexikon/gobd | 2026-10-09 | 2025-12-03 | 200 OK; corroborates AO §147 retention classes. |
| 4 | seamless-engineering/datev-extf | https://github.com/seamless-engineering/datev-extf | 2026-10-09 | 700/13 | 200 OK; EXTF schema reference for Buchungsstapel. |
| 5 | UStG (primary law) | https://www.gesetze-im-internet.de/ | 2026-10-09 | current | **404 at retrieval (re-confirmed)**. Tried `ustg`, `ustg/`, `UStG`, `ustg.html`, `ustg_2025-01-01.html`, `ustg_2024-01-01.html`, `ustg_2025-12-31.html` and the titelsuche/volltextsuche endpoints — all 404. The legal text is cited from memory and must be re-fetched before audit. |
| 6 | UStG §13 (entnommene Leistungen) | https://www.gesetze-im-internet.de/ | 2026-10-09 | current | same 404 as row 5. |
| 7 | UStG §4a (innergemeinschaftliche Leistungen) | https://www.gesetze-im-internet.de/ | 2026-10-09 | current | same 404 as row 5. |
| 8 | UStDV §23 (rounding) | https://dejure.org/gesetze/ustdv/ | 2026-10-09 | current | **404 at retrieval (re-confirmed)**. |
| 9 | AO §147 (GoBD retention) | https://dejure.org/gesetze/AO/147.html | 2026-10-09 | current | **404 at retrieval (re-confirmed)**; `ao_2025-01-01.html` also 404. |
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

## Re-verification 2026-10-15

All primary URLs re-probed with curl on **2026-10-15** (UA `Mozilla/5.0 research-bot`, `--max-time 12`, follow redirects). 56 of 69 URLs returned **200**; 3 returned **202** (eur-lex, content served); 3 returned **403** (bot-protected); 3 returned **404** (page moved); 4 returned **000** (DNS/TLS failure).

| URL | Status 2026-10-15 | Action |
|-----|-------------------|--------|
| https://www.datev.de/ | **404** | https://www.datev.de/ (SK-Schlüssel page moved) |
| https://dejure.org/gesetze/ustdv/ | **000** | https://www.gesetze-im-internet.de/ (UStDV root; 000) |
| https://www.gesetze-im-internet.de/ | **000** | https://www.gesetze-im-internet.de/ (UStG root; 000) |
| https://www.gesetze-im-internet.de/ | **000** | https://www.gesetze-im-internet.de/ (UStG root; 000) |

No fact changed as a result of this re-probe; the rows above are link-maintenance only. The KoSIT changelog URL (`itplr-kosit/.../CHANGELOG.md`) was **not** re-probed this pass (it 503'd on 2026-10-13 and is treated as unreliable); re-fetch from the raw GitHub URL before any audit.
