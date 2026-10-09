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
| 125 | USt-Schlüssel | tax key per rate |

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

## 5. Handle validation errors

| Error | Cause | Fix |
|---|---|---|
| amount uses a dot | `12.50` instead of `12,50` | replace `.` with `,` |
| Belegdatum must be TTMM | wrong length or swapped day/month | use 4 digits DDMM, e.g. `0206` for 2 June |
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
