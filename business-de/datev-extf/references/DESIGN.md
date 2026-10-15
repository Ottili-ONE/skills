# DESIGN — datev-extf

## Trigger description (draft for SKILL.md front matter)

> Use this skill when an Ottili agent must emit or consume DATEV-compatible
> machine-readable accounting data: EXTF Buchungsstapel (booking batches),
> Debitoren/Kreditoren master data, Datenservices, validation errors, or test
> fixtures. Triggers: "build a Buchungsstapel", "validate this EXTF export",
> "generate DATEV test fixtures", "DATEV rejects the Steuerschlüssel".

## What this skill does better than a generic agent

- **Column 97, not 125**: the tax key (Steuerschlüssel) sits at column 97;
  column 125 is "Abw. Skontokonto". Writing the key at index 124 makes DATEV
  silently drop the real tax key — the import proceeds with no Steuerschlüssel.
  Verified 2026-10-09 against `seamless-engineering/datev-extf src/columns.ts`.
- **TTMM Belegdatum**: day+month, 4 digits, zero-padded (`0206` = 2 June).
  The year comes from the header, never the row. A 5+ digit value or a
  swapped day/month is a hard error.
- **Comma decimals**: `12,50` not `12.50`. A dot is a hard error in DATEV's
  Prüfprogramm.
- **Automatikkonten forbid BU-Schlüssel**: ledger accounts 1000-1999 in
  SKR 03 do not accept a business unit key.
- **Category-aware validation**: header checks apply to every EXTF category;
  category-specific checks (code/name/version, column count, row rules) do
  not. A non-Buchungsstapel file must be named explicitly, not ruled against
  Buchungsstapel rules.

## Procedure outline

1. **Identify the export type** — Buchungsstapel (code 21, 125 columns) is the
   common target. Other categories: Debitoren/Kreditoren (16, v5),
   Kontenbeschriftungen (20, v1).
2. **Write the 31-field header** — Kennzeichen `EXTF`, Versionsnummer `700`,
   Formatkategorie `21`, Formatname `Buchungsstapel`, Formatversion `13`,
   Erzeugt am (17 digits), WJ-Beginn, Sachkontenlaenge, Beraternummer,
   Mandantennummer.
3. **Write the 125-column heading row** (line 2).
4. **Write booking lines** — comma decimals, S/HKennzeichen, Konto, Gegenkonto,
   Belegdatum TTMM, Buchungstext, Steuerschlüssel at column 97.
5. **Validate** — run `scripts/validate_extf.py`; every error is blocking.
6. **Generate fixtures** — valid + broken, for integration testing.

## Scripts planned

| Script | Purpose |
|---|---|
| `scripts/heading_row.py` | Emit the 31-field header and the 125-column heading row. |
| `scripts/build_stapel.py` | Build a Buchungsstapel from booking specs; emits the heading row by default (`--no-heading` to omit). |
| `scripts/validate_extf.py` | Validate an EXTF file; exits non-zero on any failure. SKR-aware Automatikkonto check; Steuerschlüssel validated at column 97. |
| `scripts/fixture_generator.py` | Generate valid + broken test fixtures. |

## Five eval prompts

1. **Build a Buchungsstapel.** "Build a stack for three bookings." → Valid CSV
   envelope, 31-field header, comma decimals, Steuerschlüssel at column 97.
   Failure sign: dot decimals; key at column 125.
2. **Steuerschlüssel fehlt.** "The validator reports the tax key is missing."
   → It is column 97, mandatory for every taxed booking line. Failure sign:
   placing it at column 125.
3. **Belegdatum format.** "Is `0206` or `0602` correct for 2 June?" → `0206`
   (TTMM, day+month). Failure sign: 5 digits; swapping day and month.
4. **Automatikkonto with BU-Schlüssel.** "Account 1500 with a business unit
   key." → Hard error. Failure sign: accepting it.
5. **Non-Buchungsstapel file.** "Validate this Debitoren export as a
   Buchungsstapel." → Say explicitly it is not a Buchungsstapel; run the
   category-specific checks instead. Failure sign: running Buchungsstapel
   rules against it.
