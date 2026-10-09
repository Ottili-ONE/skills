# SOURCES — datev-extf

Retrieval date for every entry: 2026-10-08 (re-verified **2026-10-09** for the
column-index, Belegdatum, Erzeugt am, WJ arithmetic and the full header-rule set). Versions pinned in `config/versions.json`;
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

## Conflicts / version-sensitive notes

- **Versionsnummer 700 / Formatversion 13** is verified against the
  seamless-engineering validator (EXTF_AS_OF 2026-09-25) and mrtyldr's v13
  exporter. DATEV itself does not publish a public version page; the version is
  marked **unverified until DATEV confirms** via the Prüfprogramm. Re-verify on
  every integration test run.
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
