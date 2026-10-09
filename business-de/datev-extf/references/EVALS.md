# EVALS — datev-extf

Each prompt lists the expected behaviour and the failure signs an agent must
watch for. Run the relevant script and compare the output to the expected.

## 1. Build a Buchungsstapel for three bookings
**Prompt:** "Build a Buchungsstapel for three bookings: EUR 1,200.00 net on
account 4000 with tax key 19%, EUR 500.00 on account 4200 with tax key 7%, and
EUR 100.00 on account 8000 with tax key 0%."

**Expected behaviour:** Produce a valid CSV envelope with the 31-field header
(Kennzeichen `EXTF`, Versionsnummer `700`, Formatkategorie `21`, Formatname
`Buchungsstapel`, Formatversion `13`) and all three booking lines, amounts using
a comma decimal separator. Run `scripts/validate_extf.py`; expect `ok: true`,
`errors: []`. Demonstrate `scripts/build_stapel.py --booking ...`.

**Failure signs:** Using a dot decimal separator; emitting fewer than 31 header
fields; omitting the Formatkategorie; reporting `ok: true` without running the
validator.

## 2. Validator reports "Steuerschlüssel fehlt"
**Prompt:** "My validator reports 'Steuerschlüssel fehlt'. What does that mean
and how do I fix it?"

**Expected behaviour:** Name it as the **tax key missing** (USt-Schlüssel). It
sits at **column 97** ("USt-Schlüssel (Anzahlungen)"), NOT the last column —
column 125 is "Abw. Skontokonto". Verified 2026-10-09 against
`seamless-engineering/datev-extf src/columns.ts`. State it is mandatory for every
booking line that carries a tax rate and that DATEV rejects the import without
it. Give the fix: add the correct Steuerschlüssel at column 97 for the account
(19 = `19`, 7 = `07`, 0 = `00` in SKR 03). Show the row with the key at index
96, e.g. `...;19;...` at position 97.

**Failure signs:** Describing the Steuerschlüssel as optional; placing it at
column 125 (or any index other than 96); suggesting a workaround to suppress the
error; confusing it with the BU-Schlüssel (col 9).

## 3. Pin the EXTF schema version and show a re-verification run
**Prompt:** "Pin the EXTF schema version we use and show how a re-verification
run would look."

**Expected behaviour:** Read `config/versions.json` (never hardcode) and print
the pinned Versionsnummer (`700`) and Formatversion (`13`). Mark the version
"unverified until DATEV confirms" because DATEV does not publish a public version
page. Show a dated re-verification log entry that records the run, the validator
tag, and the fixture result. Demonstrate
`scripts/validate_extf.py fixtures/buchungsstapel-valid.csv`.

**Failure signs:** Hardcoding a version in the output; omitting the
"unverified" caveat; showing a re-verification that does not re-validate the
fixtures.

## 4. Generate test fixtures for the DATEV integration
**Prompt:** "Generate test fixtures for our DATEV integration."

**Expected behaviour:** Produce a minimal valid Buchungsstapel **plus** a
deliberately broken one for negative testing. The broken one must contain a
dot-decimal amount and a malformed Belegdatum so the validator reports both
errors. Run `scripts/fixture_generator.py --out-dir ./fixtures` and confirm the
broken fixture fails validation with the expected error list.

**Failure signs:** Generating only a valid fixture; generating a broken fixture
that still validates; omitting the expected-error list.

## 5. Export 2026 accounting data for the auditor in DATEV format
**Prompt:** "Export our 2026 accounting data for the auditor in DATEV format."

**Expected behaviour:** Produce a complete, chronological, checksummed export
with a manifest (MANIFEST.json), not a raw DB dump. The export must be a valid
EXTF Buchungsstapel (run `scripts/validate_extf.py`; expect `ok: true`) and the
manifest must record SHA-256 per file and the export date.

**Failure signs:** Exporting a raw DB dump; omitting the manifest; exporting
out of chronological order; emitting a file that fails EXTF validation.


## 6. The tax key is column 97, not column 125
**Prompt:** "I put the Steuerschlüssel in the last column of the booking row.
Why does DATEV still say the tax key is missing?"

**Expected behaviour:** Explain that the Buchungsstapel has 125 columns and the
tax key is **column 97** ("USt-Schlüssel (Anzahlungen)"), not column 125
("Abw. Skontokonto"). Verified 2026-10-09 against
`seamless-engineering/datev-extf src/columns.ts`. A key written at index 124 is
read by DATEV as "Abw. Skontokonto" and the real tax key is silently dropped —
the import proceeds with no Steuerschlüssel. Give the fix: write the key at
index 96 (column 97). Demonstrate with `scripts/build_stapel.py` and confirm
with `scripts/validate_extf.py`.

**Failure signs:** Asserting the tax key is the last column; claiming DATEV
auto-detects the column; failing to run the validator on the produced file.


## Near-miss triggers

Prompts that look fine at first glance but hide a trap. The agent must catch
the trap and still produce a passing artefact.

### N1. "Build a Buchungsstapel for the whole fiscal year"
**Trap:** WJ-Beginn `20260101`, Datum vom `20260101`, Datum bis `20261231`.
**Expected behaviour:** This is **correct** — the WJ ends 2026-12-31 (wjDate +
1y − 1d). Do not flag it. The trap is the inverse: WJ `20260101` with Datum bis
`20270630`, which the validator reports as `header-beyond-wj`.

### N2. "Our booking date is 2026-06-02, put it in the Belegdatum column"
**Trap:** the row expects **TTMM** (`0206`), not `20260602`. Writing the full
date is a hard `belegdatum-format` error. The year comes from the header.

### N3. "The account is 42000, it fits fine"
**Trap:** account numbers must not exceed Sachkontenlaenge (field 14, default
4). `42000` with Sachkontenlaenge 4 is `account-too-long`. Either widen
Sachkontenlaenge (5-8) or shorten the account.

### N4. "We changed the advisor number to 8 digits"
**Trap:** Beraternummer must be 4-7 digits and >= 1001. An 8-digit value is
`header-berater`. DATEV rejects it at import.

### N5. "Generate a fixture with a dot decimal to test the validator"
**Trap:** the broken fixture must *actually* fail — `12.50` produces
`amount-dot-decimal`. A fixture that still validates is not a negative test.
