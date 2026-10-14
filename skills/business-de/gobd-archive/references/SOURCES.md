# SOURCES — gobd-archive

Retrieval date for every entry: 2026-10-09 (re-verified 2026-10-09 for AO §147 and the whk guide). Versions pinned in
`config/versions.json`; re-verify before relying on any version-sensitive fact.

| # | Source | URL | Verified version | Notes / conflicts |
|---|---|---|---|---|
| 1 | AO §147 Abs. 3 n.F. (Aufbewahrungspflichten) | https://www.gesetze-im-internet.de/ao/ | effective 2025-01-01 | **Retrieval note:** the AO index page 404'd at 2026-10-08 (site layout changed). The classes are corroborated by steuer-berater.de and whk-controlling.de. Re-fetch before an audit. |
| 2 | steuer-berater.de GoBD lexikon | https://www.steuer-berater.de/lexikon/gobd | modified 2025-12-03 | Confirms: 10y Bücher/Jahresabschlüsse, 8y Buchungsbelege, 6y andere Unterlagen/Geschäftsbriefe, all effective 01.01.2025. Also: Verfahrensdokumentation is mandatory; fines up to EUR 50,000 (§378 AO). |
| 3 | whk-controlling.de GoBD Archivierung Guide | https://www.whk-controlling.de/wissen/gobd-archivierung-guide | **re-fetched 2026-10-09** | Confirms the 8/10/6 split and "vorher 10 Jahre" for vouchers. Includes a retention calculator. |
| 4 | kostenlos-erechnung.de e-Rechnung Archivierung Pflicht | https://kostenlose-erechnung.de/ratgeber/e-rechnung-archivierung-pflicht/ | **re-fetched 2026-10-09** | Confirms 8y for Rechnungen, the original-XML-must-survive rule, and the BMF Schreiben 15.10.2025 Randziffer 60. |
| 5 | BMF Schreiben 2024-11-15 / 2025-10-15 | https://www.bmf.gv.at/ (search) | 2024-11-15, 2025-10-15 | Governs the BEG IV effective date, e-invoicing and GoBD. Re-verify annually. |
| 6 | GoBD 2014 (BMF Schreiben 14.11.2014, updated 11.03.2024) | https://www.bmf.gv.at/ (search) | 2014-11-14 / 2024-03-11 | Superseded principles retained for older retention periods. |
| 7 | BDO GoBD guidance | https://www.bdo.de/ | 2024 | Confirms immutability as a technical property (hash-chaining, append-only). |
| 8 | DATEV GoBD Leitfaden | https://www.datev.de/ | 2024 | Practical guidance; confirms the Verfahrensdokumentation checklist and export formats. |
| 9 | R3_VERIFIED_FACTS.md (Ottili planning) | ../ottili-planning/inputs/R3_VERIFIED_FACTS.md | 2026-10-06 | Internal corroboration; lists the same 8/10/6 split and the "some pages contradict" caveat. |
| 10 | EU Directive 2014/55/EU | https://ec.europa.eu/digital-building-blocks/ | EN 16931 mandate | Parent directive; audit export formats may reference it. |

| 11 | AO §147 Abs. 3 n.F. (dejure.org mirror) | https://dejure.org/gesetze/AO/147.html | effective 2025-01-01 | **Re-fetched 2026-10-09.** Page renders (JS-heavy, ad-tagged) but the text layer contains `Buchungsbeleg`, `Jahresabschluss` and `01.01.2025`. Third corroboration alongside steuer-berater.de and whk-controlling.de. The gesetze-im-internet.de AO index still 404s; dejure.org is the working mirror. |
| 12 | whk-controlling.de (verbatim quote) | https://www.whk-controlling.de/wissen/gobd-archivierung-guide | modified **2026-04-14** (re-fetched 2026-10-09) | **Verbatim:** "Seit 2025 gilt für Rechnungen und Buchungsbelege eine Aufbewahrungsfrist von 8 Jahren (vorher 10 Jahre). 10 Jahre: Für Bücher, Aufzeichnungen, Inventare, Jahresabschlüsse und Bilanzen. 8 Jahre: Für Buchungsbelege und Rechnungen. 6 Jahre: Für empfangene Handels- oder Geschäftsbriefe, Wiedergaben der abgesandten Handelsbriefe und sonstige Unterlagen mit steuerlicher Bedeutung." This is the most precise 6-year definition seen; it covers *incoming* commercial correspondence + copies of *outgoing* letters + other tax-relevant documents. |

## Conflicts / version-sensitive notes

- The retention classes are **verified by three independent sources** (steuer-berater.de, whk-controlling.de, dejure.org AO §147 mirror), all effective 2025-01-01 (10y books/annual accounts, 8y
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

## Re-check 2026-10-13 (PASS 3 of skills-business-de-r3-01)

Two random sources per skill re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-13. Nothing was copied verbatim from any source; all SKILL.md prose is original.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://www.steuer-berater.de/lexikon/gobd | 200 | GoBD lexicon resolves; 10-year retention for books/records under AO/HGB confirmed |
| https://www.gesetze-im-internet.de/ao/ | 404 | AO page 404 at retrieval (re-confirmed); cited from the 2026-10-09 record |

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
