# Procedures — datev-extf

All versions are read from `config/versions.json`. Never hardcode a version in
this file or in scripts. The EXTF schema version (Versionsnummer `700`,
Formatversion `13`) is marked **unverified until DATEV confirms** because
DATEV does not publish a public version page.

## 1. Identify the export type

| Type | Formatkategorie | Use case |
|---|---|---|
| Buchungsstapel | 21 | common integration target |
| Debitoren/Kreditoren | 16 | customer/supplier master data |
| Buchungsstapel | 21 | booking rows |
| Debitoren/Kreditoren | 16 | customer/supplier master data |
| Kontenbeschriftungen | 20 | account labels |

## 2. Build the EXTF header (line 1, 31 fields)

The header is a single semicolon-delimited row. Mandatory fields. Verified
2026-10-09 against seamless-engineering/datev-extf `src/extf.ts` (the rules
DATEV itself does not publish publicly):

| Pos | Field | Value |
|---|---|---|
| 1 | Kennzeichen | `EXTF` |
| 2 | Versionsnummer | `700` (pinned) |
| 3 | Formatkategorie | `21` |
| 4 | Formatname | `Buchungsstapel` |
| 5 | Formatversion | `13` |
| 6 | Erzeugt am | 17 digits YYYYMMDDHHMMSS000 |
| 11 | Beraternummer | 4-7 digits, >= 1001 |
| 12 | Mandantennummer | 1-5 digits, >= 1 |
| 13 | WJ-Beginn | fiscal year start YYYYMMDD |
| 14 | Sachkontenlaenge | **4-8** (default 4) |
| 15-16 | Datum vom/bis | booking period YYYYMMDD, same WJ, from <= to |
| 17 | Bezeichning | label, <= 30 chars |
| 21 | Festschreibung | `1` |
| 22 | WKZ | `EUR` (3 uppercase letters if present) |
| 27 | Sachkontenrahmen | `03` or `04` |

**WJ arithmetic:** the fiscal year ends the day *before* the next WJ anniversary.
For WJ-Beginn `20260101` the WJ end is `2026-12-31`, not `2026-01-01`. Datum
vom/bis must lie inside that window. This is the check that catches a
WJ-Beginn of `20260101` with Datum bis `20260630` — which is *correct* — and
one with `20270630` — which is an error (`header-beyond-wj`).

Line 2 is the 125-column heading row; lines 3+ are booking rows.

## 3. Assemble the Buchungsstapel

Each booking row has 125 columns. Mandatory columns:

| Col | Field | Rule |
|---|---|---|
| 1 | Umsatz | comma decimal, e.g. `12,50` |
| 2 | Soll/Haben-Kennzeichen | `S` or `H` |
| 7 | Konto | must fit Sachkontenlaenge |
| 9 | BU-Schlüssel | **forbidden on Automatikkonten** (1000-1999 in SKR 03) |
| 10 | Belegdatum | **TTMM** (day+month, 4 digits, e.g. `0206`); the year comes from the header |
| 14 | Buchungstext | quoted text |
| 97 | USt-Schlüssel (Anzahlungen) | tax key per rate | mandatory |
| 103 | Buchungs GUID | booking GUID | optional |

## 4. Validate

Run `scripts/validate_extf.py`. Every error is blocking. Map each error code
to a fix — never guess. The validator checks:

- Kennzeichen is `EXTF`
- Versionsnummer matches the pinned value
- Formatkategorie is `21` and Formatname is `Buchungsstapel`
- Formatversion is `13`
- Amounts use a comma decimal separator
- Belegdatum is exactly 4 digits TTMM (day+month, zero-padded); the year comes from the header (WJ-Beginn / Datum vom/bis), not from the row.
- Erzeugt am (header field 6) is exactly 17 digits YYYYMMDDHHMMSS000.
- Soll/Haben is `S` or `H`

## 4b. Worked examples

### Good — valid Buchungsstapel

```
EXTF;700;21;Buchungsstapel;13;20261009105214000;;;;;29098;55003;20260101;4;
20260601;20260630;Shop 06/2026;;1;EUR;;;;03;;;;;;;
Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;... (125 cols) ...
12,50;S;;;;;4000;;;0206;;;Netto+19%;;;;...;;;19
```

`scripts/validate_extf.py` reports `ok: true, error_count: 0`.

### Bad — WJ-Beginn inconsistent with the booking period

```
EXTF;...;20260101;4;20270601;20270630;...
```

The validator reports `header-beyond-wj` (Datum bis 2027-06-30 is outside the
WJ that ends 2026-12-31). A common trap: keeping the WJ at the invoice year
while the export period rolls into the next year.

### Bad — Belegdatum year confusion

Row `Belegdatum = 0206` with WJ-Beginn `20260101` means **2 June 2026**.
The year is *never* in the row. Writing `20260602` there is a hard error
(`belegdatum-format`: must be exactly 4 digits).

## 4c. Datenservices (other Formatkategorien)

The Buchungsstapel (category 21) is the common integration target. DATEV ships
these other exports through the same EXTF envelope — same 31-field header,
different Formatkategorie/Formatname/Formatversion and a different column
count. Verified 2026-10-09 against seamless-engineering/datev-extf
`src/extf.ts` (the `Category` enum and the debkred text-field list):

| Formatkategorie | Formatname | Formatversion | Content | Columns |
|---|---|---|---|---|
| 21 | Buchungsstapel | 13 | booking rows | 125 |
| 16 | Debitoren/Kreditoren | 5 | customer/supplier master data | per DEBKRED spec |
| 20 | Kontenbeschriftungen | 1 | account labels | per spec |



## 5. Handle validation errors

| Error | Cause | Fix |
|---|---|---|
| amount uses a dot | `12.50` instead of `12,50` | replace `.` with `,` |
| Belegdatum must be TTMM | wrong length or swapped day/month | use 4 digits DDMM, e.g. `0206` for 2 June |
| Soll/Haben invalid | not `S` or `H` | use `S` for debit, `H` for credit |
| header too short | fewer than 31 fields | pad to 31 fields |
| BU-Schlüssel on Automatikkonto | col 9 populated on a ledger account | remove the BU-Schlüssel |
| Steuerschlüssel at the wrong column | key written at col 125 instead of col 97 | write it at index 96 (column 97) |

**Error-code contract.** `scripts/validate_extf.py` emits these codes; the
table above is the human-readable version. If a code appears that is not
listed here, re-run the validator and read the code before inventing a fix —
the list is the contract, not memory. Verified 2026-10-15 by grepping the
`add(findings, ...)` calls in `scripts/validate_extf.py`.

| Code | Severity | Meaning |
|---|---|---|
| `kennzeichen` | error | header field 1 is not `EXTF` |
| `versionsnummer` | error | header field 2 does not match the pinned version |
| `formatkategorie` | error | header field 3 is not `21` |
| `formatname` | error | header field 4 is not `Buchungsstapel` |
| `formatversion` | error | header field 5 is not `13` |
| `erzeugt-am-format` | error | header field 6 is not 17 digits YYYYMMDDHHMMSS000 |
| `festschreibung` | error | header field 21 is not `1` |
| `header-berater` | error | Beraternummer is not 4-7 digits or < 1001 |
| `header-mandant` | error | Mandantennummer is not 1-5 digits or < 1 |
| `header-currency` | error | WKZ (field 22) is not a 3-letter code |
| `header-date` | error | Datum vom/bis (fields 15-16) is not YYYYMMDD |
| `header-dates-order` | error | Datum vom is after Datum bis |
| `header-dates-year` | error | Datum vom/bis year differs from the WJ year |
| `header-beyond-wj` | error | Datum bis is after the WJ end |
| `header-before-wj` | error | Datum vom is before the WJ start |
| `header-too-short` | error | fewer than 31 header fields |
| `header-skl-missing` | warning | Sachkontenlaenge (field 14) empty |
| `header-skl` | error | Sachkontenlaenge not in 4-8 |
| `header-label` | warning | Bezeichnung (field 17) longer than 30 chars |
| `header-skr` | warning | Sachkontenrahmen (field 27) not `03`/`04` |
| `heading-column-count` | warning | line 2 is not 125 columns |
| `no-headings` | warning | line 2 is blank |
| `booking-column-count` | error | a booking row is not exactly 125 columns |
| `amount-dot-decimal` | error | col 1 uses a dot decimal separator |
| `side-invalid` | error | col 2 is not `S` or `H` |
| `belegdatum-format` | error | col 10 is not exactly 4 digits TTMM |
| `belegdatum-impossible` | warning | col 10 is 4 digits that are not a real calendar day |
| `account-too-long` | warning | col 7 is longer than Sachkontenlaenge |
| `bu-on-automatic-account` | error | col 9 is not `40` on an Automatikkonto |
| `taxkey-invalid` | error | col 97 holds a value outside the SKR tax-key set |
| `taxkey-missing` | error | col 97 is empty on a non-blank booking row |

## 6. Generate test fixtures

Run `scripts/fixture_generator.py --out-dir ./fixtures`. Produces:

- `buchungsstapel-valid.csv` — minimal valid Buchungsstapel
- `buchungsstapel-broken.csv` — deliberately broken (dot decimal + malformed
  Belegdatum) for negative testing

Both are deterministic and runnable offline.

## 7. Export for audit

Produce a complete, chronological, checksummed export with a manifest
(MANIFEST.json), not a raw DB dump.
