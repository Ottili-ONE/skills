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
| Einzelnachweis | 21 | single booking |
| Saldenliste / Kontenrahmen | 20 | ledger balances |

## 2. Build the EXTF header (line 1, 31 fields)

The header is a single semicolon-delimited row. Mandatory fields:

| Pos | Field | Value |
|---|---|---|
| 1 | Kennzeichen | `EXTF` |
| 2 | Versionsnummer | `700` (pinned) |
| 3 | Formatkategorie | `21` |
| 4 | Formatname | `Buchungsstapel` |
| 5 | Formatversion | `13` |
| 6 | Erzeugt am | YYYYMMDD |
| 11 | Beraternummer | advisor number |
| 12 | Mandantennummer | client number |
| 13 | WJ-Beginn | fiscal year start YYYYMMDD |
| 14 | Sachkontenlaenge | account length (default 4) |
| 15-16 | Datum vom/bis | booking period YYYYMMDD |
| 17 | Bezeichnung | label |
| 21 | Festschreibung | `1` |
| 22 | WKZ | `EUR` |
| 27 | Sachkontenrahmen | `03` or `04` |

Line 2 is the 125-column heading row; lines 3+ are booking rows.

## 3. Assemble the Buchungsstapel

Each booking row has 125 columns. Mandatory columns:

| Col | Field | Rule |
|---|---|---|
| 1 | Umsatz | comma decimal, e.g. `12,50` |
| 2 | Soll/Haben-Kennzeichen | `S` or `H` |
| 7 | Konto | must fit Sachkontenlaenge |
| 9 | BU-Schlüssel | **forbidden on Automatikkonten** (1000-1999 in SKR 03) |
| 10 | Belegdatum | YYYYMMDD with leading zeros |
| 14 | Buchungstext | quoted text |
| 125 | USt-Schlüssel | tax key per rate |

## 4. Validate

Run `scripts/validate_extf.py`. Every error is blocking. Map each error code
to a fix — never guess. The validator checks:

- Kennzeichen is `EXTF`
- Versionsnummer matches the pinned value
- Formatkategorie is `21` and Formatname is `Buchungsstapel`
- Formatversion is `13`
- Amounts use a comma decimal separator
- Belegdatum is exactly 8 digits YYYYMMDD
- Soll/Haben is `S` or `H`

## 5. Handle validation errors

| Error | Cause | Fix |
|---|---|---|
| amount uses a dot | `12.50` instead of `12,50` | replace `.` with `,` |
| Belegdatum must be YYYYMMDD | missing leading zero or wrong format | zero-pad to 8 digits |
| Soll/Haben invalid | not `S` or `H` | use `S` for debit, `H` for credit |
| header too short | fewer than 31 fields | pad to 31 fields |
| BU-Schlüssel on Automatikkonto | col 9 populated on a ledger account | remove the BU-Schlüssel |

## 6. Generate test fixtures

Run `scripts/fixture_generator.py --out-dir ./fixtures`. Produces:

- `buchungsstapel-valid.csv` — minimal valid Buchungsstapel
- `buchungsstapel-broken.csv` — deliberately broken (dot decimal + malformed
  Belegdatum) for negative testing

Both are deterministic and runnable offline.

## 7. Export for audit

Produce a complete, chronological, checksummed export with a manifest
(MANIFEST.json), not a raw DB dump.
