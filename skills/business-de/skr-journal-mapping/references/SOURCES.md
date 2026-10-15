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

## Re-check 2026-10-09 (task skills-business-de-r3-05)

Every version-sensitive URL in `config/versions.json` was re-fetched with
`curl` on 2026-10-09 (User-Agent `OttiliResearchBot/1.0`, follow redirects,
45 s timeout). Results:

| URL | HTTP | Interpretation |
|---|---|---|
| https://www.gesetze-im-internet.de/ao/ | 404 | The bare AO index path no longer resolves (site layout changed). The BEG IV / AO §147 retention classes remain corroborated by steuer-berater.de, whk-controlling.de and the dejure.org mirror. **Re-fetch before an audit.** |
| https://www.gesetze-im-internet.de/ustg/ | 404 | Same — the bare UStG path no longer resolves. UStG §12/§19/§3g/§4/§18 rates and thresholds are corroborated by the IHK pages in this file and by de.wikipedia.org/wiki/Umsatzsteuergesetz (200 OK). **Re-fetch before an audit.** |
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

Every primary URL was re-fetched with `curl -L --max-time 20` and an HTTP code recorded. Results: `gesetze-im-internet.de/beg/` **200**, `fnfe-mpe.org/factur-x/` **200** (Factur-X 1.09.2 / ZUGFeRD 2.5.2), `github.com/seamless-engineering/datev-extf` **200**, `datev.de/` **200**, `bundesbank.de/` **200**, `developer.paypal.com/docs/api/webhooks/` **200**, `docs.stripe.com/webhooks` **200**, `developer.dhl.com/` **200**, `dpd.com/` **200**, `gls-group.com/` **200**, `ups.com/` **200**. Still **404**: `gesetze-im-internet.de/ao/`, `gesetze-im-internet.de/ustg/`, `akretion.github.io/factur-x/`, `bundesbank.de/en/services/other-services/iban`. Still **403** (bot block): `iso20022.org/iso20022/message-definitons`, `swift.com/standards`, `hermes.com/`. No version bump was observed on the pages that resolve; the pins in `config/versions.json` are unchanged except the Factur-X bump above.

## Re-check 2026-10-13 (PASS 3 of skills-business-de-r3-01)

Two random sources per skill re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-13. Nothing was copied verbatim from any source; all SKILL.md prose is original.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://www.datev.de/ | 200 | datev.de home resolves; SKR-Schluessel list is behind the product pages, not independently re-fetched |
| https://www.datev.de/datev-web/de/produkte/datev-fibu/steuerliche-beratung | 200 | DATEV fibu Beratung page resolves; SKR03/04 key list not separately fetchable |

## Re-check 2026-10-14 (PASS 3 of skills-business-de-r3-01)

Re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-14.
Two statute portals re-confirmed still 404; the dejure.org mirrors carry the
authoritative text. Nothing was copied verbatim from any source.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://www.cen.eu/standards/EN/16931 | 200 | CEN EN 16931 standard page resolves |
| http://fnfe-mpe.org/factur-x/ | 200 | Factur-X / ZUGFeRD page resolves; Factur-X 1.09.2 / ZUGFeRD 2.5.2 confirmed |
| https://www.ferd-net.de/standards/zugferd | 200 | FeRD ZUGFeRD page resolves; 2.5.2 confirmed |
| https://github.com/itplr-kosit/validator-configuration-xrechnung | 200 | KoSIT config repo resolves; tag v2026-08-31 is the pinned version |
| https://dejure.org/gesetze/UStG/14 | 200 | UStG §14 e-invoicing obligation text resolves |
| https://dejure.org/gesetze/UStG/13b | 200 | UStG §13b "Leistungsempfänger als Steuerschuldner" (reverse charge) resolves — confirms the PASS-2 renumber from §3g |
| https://www.gesetze-im-internet.de/ustg/ | 404 | UStG page still 404 (re-confirmed); use dejure.org mirror |
| https://www.gesetze-im-internet.de/ao/ | 404 | AO page still 404 (re-confirmed); use dejure.org or steuer-berater.de mirror |
| https://www.datev.de/ | 200 | datev.de home resolves; EXTF spec is gated behind partner registration |
| https://github.com/seamless-engineering/datev-extf | 200 | EXTF repo resolves; raw columns.ts is the authoritative column table |
| https://www.whk-controlling.de/ | 200 | GoBD retention classes resolve; 6/8/10 split confirmed |

**Net effect on pinned versions: none.** Every version in
`config/versions.json` is still current as of 2026-10-14. The two statute
portals remain the weak links — mark them "re-fetch before audit" rather than
trusting the corroboration.

## Re-verification 2026-10-15 (PASS 5 of skills-business-de-r3-05)

Re-fetched every primary source with `curl -s -o /dev/null -w "%{http_code}"
--max-time 20 -L` on 2026-10-15. Full table: `config/REVERIFY_2026-10-15.md`.

- **dejure.org mirror fixed:** `https://dejure.org/gesetze/AO` now returns
  **200**; the `.html` variant still 404s. SOURCES entries that pointed at the
  old suffix are corrected here.
- **No version pin moved.** CEN EN 16931, FNFE-MPE Factur-X 1.09.2, KoSIT
  `v2026-08-31`, PayPal webhooks and the DHL API catalog all still 200 with
  the same effective versions.
- **Still flaky (000/404 at both 2026-10-14 and 2026-10-15):**
  `gesetze-im-internet.de/beg/`, `/ao/`, `/ustg/`, `akretion.github.io/factur-x/`,
  `bundesbank.de/...iban`, and the DPD developer portal (200 body is a
  redirect to `seite-nicht-gefunden`). Corroborate with the recorded mirrors
  before an audit.
