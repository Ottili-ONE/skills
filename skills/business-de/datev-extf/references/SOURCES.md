# SOURCES — datev-extf

Retrieval date for every entry: 2026-10-09 (re-verified **2026-10-09** for the
column-index, Belegdatum, Erzeugt am, WJ arithmetic and the full header-rule set;
**re-verified again 2026-10-09** for the Datenservices table and the column-97
tax-key fix). Versions pinned in `config/versions.json`;
re-verify before relying on any version-sensitive fact.

| # | Source | URL | Verified version | Notes / conflicts |
|---|---|---|---|---|
| 1 | DATEV EXTF Formatbeschreibung (developer.datev.de) | https://developer.datev.de/ | not fetched (200 but empty body at 2026-10-08) | **Retrieval note:** the developer portal returns an empty 200 body; the EXTF spec is gated behind partner registration. The field/column model is corroborated by the seamless-engineering validator, which states its rules come from DATEV's Formatbeschreibung and the DATEV-Format Prüfprogramm. |
| 2 | seamless-engineering/datev-extf (TypeScript validator) | https://github.com/seamless-engineering/datev-extf | EXTF_AS_OF 2026-09-25 | Primary corroboration: 125-column Buchungsstapel heading row, header field model, and error codes. MIT licensed. **Re-fetched 2026-10-09 (full `src/extf.ts` read):** in addition to the column indices, re-verified (a) `Erzeugt am` regex `/^20\d{15}$/`; (b) **WJ end = wjDate + 1y - 1d** (so WJ 2026-01-01 ends 2026-12-31, NOT 2026-01-01); (c) header-date / header-dates-order / header-dates-year / header-before-wj / header-beyond-wj rules; (d) Beraternummer `/^\d{4,7}$/` >= 1001; (e) Mandantennummer `/^\d{1,5}$/` >= 1; (f) Sachkontenlaenge must be 4-8 (else `header-skl` error); (g) WKZ `/^[A-Z]{3}$/`; (h) Bezeichnung > 30 chars is a warning; (i) Sachkontenrahmen must be 2 digits (warning); (j) Automatikkonten list (SKR 03/04, Gueltig 2026, Art.-Nr. 11174/11175) with BU-Schluessel "40" allowed. |
| 3 | DATEV-Format Prüfprogramm field definitions | shipped with the Prüfprogramm | Formatversion 13 | The validator's second source; confirms Formatversion 13 is current (10-12 are warnings). |
| 4 | DATEV Hilfe-Center `#REW` import messages | https://hilfe.datev.de/ | 2026-10-08 | Third source for the validator; where the three disagree, the check is a warning, not an error. |
| 5 | ameax/datev-extf (CSV writer) | https://github.com/ameax/datev-extf | 2026-10-08 | Corroboration of the CSV envelope shape and the comma-decimal convention. |
| 6 | mrtyldr/datev-exporter (Java) | https://github.com/mrtyldr/datev-exporter | v12/v13 | Corroboration of the Buchungsstapel v13 column set and the Automatikkonten BU-Schlüssel rule. |
| 7 | R3_VERIFIED_FACTS.md (Ottili planning) | ../ottili-planning/inputs/R3_VERIFIED_FACTS.md | 2026-10-06 | Internal corroboration: EXTF header example "EXTF";700;21;"Buchungsstapel";9;... and the Datenservices note. |
| 8 | DATEV Buchungsdatenservice | https://www.datev.de/web/de/marktplatz/marahplus/ | 2026-10-08 | Confirms EXTF is the file-based basis and a REST variant exists (accounting:extf-files). |
| 9 | DATEV Rechnungsdatenservice 1.0 | https://www.datev.de/web/de/marktplatz/marahplus/ | 2026-10-08 | Confirms the XML-Schnittstelle online basis and the booking-suggestion flow. |
| 10 | sc-umsatzsteuerberatung/datev-extf (Dart) | https://github.com/sc-umsatzsteuerberatung/datev-extf | 2026-10-08 | Corroboration of the parser/serializer shape and the Steuerschlüssel field. |
| 11 | seamless-engineering/datev-extf `src/columns.ts` (raw) | https://raw.githubusercontent.com/seamless-engineering/datev-extf/main/src/columns.ts | EXTF_AS_OF 2026-09-25 | **Re-fetched 2026-10-09 (full read).** This is the source that settled the column-index question. `BUCHUNGSSTAPEL_COLUMNS` (125 entries) gives: col 1 = "Umsatz (ohne Soll/Haben-Kz)", col 2 = "Soll/Haben-Kennzeichen", col 7 = "Konto", col 8 = "Gegenkonto (ohne BU-Schlüssel)", col 9 = "BU-Schlüssel", col 10 = "Belegdatum", col 14 = "Buchungstext", col 37 = "KOST1 - Kostenstelle", **col 97 = "USt-Schlüssel (Anzahlungen)"** (the tax key), col 103 = "Buchungs GUID", col 125 = "Abw. Skontokonto". `BUCHUNGSSTAPEL_COLUMN_COUNT = {10:120, 11:122, 12:124, 13:125}`. `DEBKRED_COLUMNS` (254 entries) = Debitoren/Kreditoren Formatversion 5. `FORMAT_NAMES = {"21":"Buchungsstapel","16":"Debitoren/Kreditoren","20":"Kontenbeschriftungen"}` — **category 20 is "Kontenbeschriftungen" (account labels), not "Saldenliste/Kontenrahmen", and there is no "Einzelnachweis" category**; both were corrected 2026-10-09. |

## Conflicts / version-sensitive notes

- **Versionsnummer 700 / Formatversion 13** is verified against the
  seamless-engineering validator (EXTF_AS_OF 2026-09-25) and mrtyldr's v13
  exporter. DATEV itself does not publish a public version page; the version is
  marked **unverified until DATEV confirms** via the Prüfprogramm. Re-verify on
  every integration test run.
- **The tax key is column 97, not column 125.** Verified 2026-10-09 against
  `src/columns.ts` (col 97 = "USt-Schlüssel (Anzahlungen)", col 125 = "Abw. Skontokonto").
  `fixture_generator.py` and `build_stapel.py` previously wrote the key at index
  124, which DATEV reads as "Abw. Skontokonto" and drops the real tax key
  silently. Corrected 2026-10-09.
- The 125-column Buchungsstapel heading row is copied verbatim from DATEV's
  Musterdaten as of 2024 per the seamless-engineering source. If DATEV changes
  the heading row, the validator warns rather than errors.
- The Automatikkonten BU-Schlüssel rule (ledger accounts 1000-1999 in SKR 03)
  is corroborated by two independent validators; treat as verified.
- Amounts use a comma decimal separator; the dot-vs-comma error is the most
  common import rejection and is verified against the validator's `#REW`
  messages.
- **Belegdatum is TTMM (day+month, 4 digits), not YYYYMMDD.** Verified
  2026-10-09 against `src/extf.ts` line 692 ("Belegdatum as day and month") and
  the writer at line 760 (`fields[10]`). The year is taken from the header, so
  `0206` means 2 June of the header's fiscal year. Earlier drafts of this skill
  (and the `build_stapel.py` example) wrongly used YYYYMMDD; corrected 2026-10-09.
- **Erzeugt am is 17 digits** (YYYYMMDDHHMMSS000), per `src/extf.ts` line 305
  (`/^20\d{15}$/`), not 8. Corrected 2026-10-09.

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
| https://developer.datev.de/ | 200 | DATEV developer portal resolves; EXTF spec is gated behind partner registration |
| https://raw.githubusercontent.com/seamless-engineering/datev-extf/main/src/columns.ts | 200 | raw columns.ts fetched; col 97 = USt-Schluesel (Anzahlungen), col 125 = Abw. Skontokonto |

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
