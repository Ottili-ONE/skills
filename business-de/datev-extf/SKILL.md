---
name: datev-extf
description: "Produce and validate DATEV EXTF (Exportdateiformat) booking stacks and data exports for German accounting integrations: EXTF header fields, Buchungsstapel structure, Datenservices, validation errors, and test fixtures. Use when an agent must emit or consume DATEV-compatible machine-readable accounting data, validate a booking stack, or build test fixtures for DATEV integration."
license: MIT-compat
compatibility: "framework-agnostic; DATEV EXTF 700/13; offline validation"
metadata: {}
allowed-tools: []
---

# datev-extf

## When to use this skill

Use this skill when an agent must emit or consume DATEV-compatible machine-readable
accounting data: EXTF (Exportdateiformat) Buchungsstapel (booking batches),
Debitoren/Kreditoren master data, Datenservices, validation errors, or test
fixtures for a DATEV integration. Do **not** use it for non-DATEV CSV, generic
accounting XML, or exports that are not consumed by DATEV software.

## Description

Produce and validate DATEV EXTF (Exportdateiformat) booking stacks and data
exports for German accounting integrations: EXTF header fields,
Buchungsstapel structure, Datenservices, validation errors, and test fixtures.
Use when an agent must emit or consume DATEV-compatible machine-readable accounting
data, validate a booking stack, or build test fixtures for DATEV integration.

## Procedure

1. **Identify the export type** — single booking (Einzelnachweis), booking stack
   (Buchungsstapel), or full ledger export (Saldenliste/Kontenrahmen). The
   Buchungsstapel is the common integration target.
2. **Build the EXTF header** — the header is line 1 of the CSV, 31 mandatory
   fields. Key fields: Kennzeichen (must be `EXTF`), Versionsnummer (must be
   `700`), Formatkategorie (must be `21` for Buchungsstapel), Formatname
   (must be `Buchungsstapel`), Formatversion (must be `13`), Erzeugt am
   Erzeugt am (17 digits YYYYMMDDHHMMSS000), Herkunft, Exportiert von, Importiert von,
   Beraternummer, Mandantennummer, WJ-Beginn, Sachkontenlaenge, Datum vom,
   Datum bis, Bezeichnung, Diktatkuerzel, Festschreibung, WKZ,
   Sachkontenrahmen, Anwendungsinformation. Pin the schema version in config;
   never hardcode.
3. **Assemble the Buchungsstapel** — one CSV envelope per file; each booking line
   has: Buchungstext, Betrag (amount, comma decimal), Konto (account), Kst (cost
   center), Steuerschlüssel (tax key), MwSt (VAT), Belegdatum, Buchungsdatum.
   Validate every field against the EXTF schema.
4. **Validate** — run the EXTF schema validation (XSD or the DATEV SDK validator).
   Treat every schema error as blocking; map each error code to a fix.
5. **Handle validation errors** — common errors: missing Steuerschlüssel, invalid
   account number (plausibility check), wrong amount format (dot instead of
   comma), wrong date format (missing leading zero), duplicate Belegnummer.
   Each error has a specific fix; never guess.
6. **Generate test fixtures** — produce a minimal valid Buchungsstapel plus a
   deliberately broken one for negative testing. Fixtures must be deterministic
   and runnable offline.
7. **Export for audit** — produce a complete, chronological, checksummed export
   covering the retention period, with a manifest.

## Decision tables

### EXTF header fields (Buchungsstapel)

| Field | Meaning | Mandatory |
|---|---|---|
| Kennzeichen (field 1) | "EXTF" | yes |
| Versionsnummer (field 2) | "700" | yes |
| Formatkategorie (field 3) | "21" = Buchungsstapel | yes |
| Formatname (field 4) | "Buchungsstapel" | yes |
| Formatversion (field 5) | "13" | yes |
| Erzeugt am (field 6) | 17 digits YYYYMMDDHHMMSS000 | yes |
| Herkunft (field 8) | sender id | yes |
| Beraternummer (field 11) | advisor number | yes |
| Mandantennummer (field 12) | client number | yes |
| WJ-Beginn (field 13) | fiscal year start YYYYMMDD | yes |
| Sachkontenlaenge (field 14) | account length, **4-8** (default 4) | yes |
| Datum vom/bis (fields 15-16) | from/to YYYYMMDD, same WJ, from <= to | yes |
| Beraternummer (field 11) | 4-7 digits, >= 1001 | yes |
| Mandantennummer (field 12) | 1-5 digits, >= 1 | yes |
| WKZ (field 22) | 3 uppercase letters if present | yes |
| Bezeichnung (field 17) | label | yes |
| Sachkontenrahmen (field 27) | SKR (03/04) | yes |


### Buchungsstapel booking-line fields (Formatversion 13, 125 columns)

| Column | Field | Meaning | Notes |
|---|---|---|---|
| 1 | Umsatz | amount (debit/credit net) | comma decimal, e.g. 12,50 |
| 2 | Soll/Haben-Kennzeichen | "S" (Soll) or "H" (Haben) | mandatory |
| 3 | WKZ Umsatz | currency | EUR default |
| 7 | Konto | account number | must fit Sachkontenlaenge |
| 8 | Gegenkonto | contra account | omit BU-Schlüssel here |
| 9 | BU-Schlüssel | business unit key | **forbidden on Automatikkonten** |
| 10 | Belegdatum | voucher date | **TTMM** (day+month, 4 digits, e.g. `0206` for 2 June); the year comes from the header, not the row |
| 14 | Buchungstext | booking text | quoted |
| 35 | KOST1 - Kostenstelle | cost center | optional |
| 97 | USt-Schlüssel (Anzahlungen) | tax key per rate | **mandatory** |
| 103 | Buchungs GUID | booking GUID | optional |

Line 2 of the file is the 125-column heading row; line 1 is the 31-field header.

## Pitfalls from research

- Amounts use a **comma** decimal separator (12,50); a dot (12.50) is a hard
  error in DATEV's Prüfprogramm.
- Belegdatum is **TTMM** (day+month, 4 digits, zero-padded, e.g. `0206` for 2 June). The year is taken from the header (WJ-Beginn / Datum vom), never from the row. A 5+ digit value or a swapped day/month is a hard error. Verified 2026-10-09 against seamless-engineering/datev-extf (Belegdatum as day and month).
- Automatikkonten (ledger accounts 1000-1999 in SKR 03) do not accept a
  BU-Schlüssel (business unit key) — adding one is a hard error.
- Account numbers must not exceed Sachkontenlaenge; too-long account numbers
  are rejected at import.
- DATEV does not publish a public version page for EXTF; the schema version
  (Versionsnummer 700 / Formatversion 13) is marked "unverified until DATEV
  confirms" via the Prüfprogramm and must be re-verified on every integration
  test run.
- **The Steuerschlüssel is column 97, not column 125.** Verified 2026-10-09
  against `seamless-engineering/datev-extf src/columns.ts`: col 97 =
  "USt-Schlüssel (Anzahlungen)" (the tax key), col 125 = "Abw. Skontokonto".
  Writing the key at index 124 makes DATEV read it as "Abw. Skontokonto" and
  silently drop the real tax key — the import proceeds with no Steuerschlüssel.
  `fixture_generator.py` and `build_stapel.py` previously wrote it at index 124;
  corrected 2026-10-09.

## Verification checklist

- [ ] Export type identified (Buchungsstapel / Debitoren / Kreditoren)
- [ ] Header fields complete and version pinned from config
- [ ] Amounts use comma decimal separator
- [ ] Belegdatum is 4-digit TTMM (day+month) with leading zeros
- [ ] Erzeugt am is 17 digits (YYYYMMDDHHMMSS000)
- [ ] WJ-Beginn parses; Datum vom/bis inside the WJ, same year, from <= to
- [ ] Sachkontenlaenge is 4-8; account numbers fit it
- [ ] Beraternummer (4-7 digits, >= 1001) and Mandantennummer (>= 1) valid
- [ ] No BU-Schlüssel on Automatikkonten
- [ ] Validator returns 0 errors (all errors blocking)
- [ ] Test fixtures generated (valid + broken)
- [ ] Audit export is chronological, checksummed, with a manifest

## Datenservices (other Formatkategorien)

The Buchungsstapel (code 21) is the common integration target. DATEV also
ships these other exports through the same EXTF envelope — the identical
31-field header, but a different category code, name, version and column
count:

| Code | Name | Ver. | Content | Columns |
|---|---|---|---|---|
| 21 | Buchungsstapel | 13 | booking rows | 125 |
| 16 | Debitoren/Kreditoren | 5 | customer/supplier master data | per DEBKRED spec |
| 20 | Kontenbeschriftungen | 1 | account labels | per spec |

Header-level checks (Kennzeichen, Versionsnummer, Erzeugt am, WJ,
Sachkontenlaenge, Berater, Mandant) apply to **every** category. The
category-specific checks (code/name/version, column count, row rules) do
**not**. When a file is not a Buchungsstapel, say so explicitly instead of
running Buchungsstapel rules against it.

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
