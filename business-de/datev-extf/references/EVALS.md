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

**Expected behaviour:** Name it as the **tax key missing** (USt-Schlüssel, the
last column of the Buchungsstapel, col 125). State it is mandatory for every
booking line that carries a tax rate and that DATEV rejects the import
without it. Give the fix: add the correct Steuerschlüssel for the account (19 =
`19`, 7 = `07`, 0 = `00` in SKR 03).

**Failure signs:** Describing the Steuerschlüssel as optional; suggesting a
workaround to suppress the error; confusing it with the BU-Schlüssel (col 9).

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
