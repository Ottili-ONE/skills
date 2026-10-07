# DESIGN: datev-extf

## Trigger description (SKILL.md description draft, ≤1024 chars)
"Produce and validate DATEV EXTF (Exportdateiformat) booking stacks and data exports for German accounting integrations: EXTF header fields, Buchungsstapel structure, Datenservices, validation errors, and test fixtures. Use when an agent must emit or consume DATEV-compatible machine-readable accounting data, validate a booking stack, or build test fixtures for DATEV integration."

## Procedure outline
1. **Identify the export type** — single booking (Einzelnachweis), booking stack (Buchungsstapel), or full ledger export (Saldenliste/Kontenrahmen). The Buchungsstapel is the common integration target.
2. **Build the EXTF header** — mandatory header fields: Formatkennzeichen (format identifier), Version (schema version, pinned in config), Erstellungsdatum (creation date), Absender (sender), etc. Pin the schema version in config; never hardcode.
3. **Assemble the Buchungsstapel** — one XML envelope per file; each booking line has: Buchungstext, Betrag (amount), Konto (account), Kst (cost center), Steuerschlüssel (tax key), MwSt (VAT), Belegdatum, Buchungsdatum. Validate every field against the EXTF schema.
4. **Validate** — run the EXTF schema validation (XSD or the DATEV SDK validator). Treat every schema error as blocking; map each error code to a fix.
5. **Handle validation errors** — common errors: missing Steuerschlüssel, invalid account number (plausibility check), wrong amount format, wrong date format, duplicate Belegnummer. Each error has a specific fix; never guess.
6. **Generate test fixtures** — produce a minimal valid Buchungsstapel plus a deliberately broken one for negative testing. Fixtures must be deterministic and runnable offline.
7. **Export for audit** — produce a complete, chronological, checksummed export covering the retention period, with a manifest.

## Scripts planned
- `scripts/validate_extf.py` — validates a Buchungsstapel against the pinned EXTF schema; emits a machine-readable pass/fail JSON plus the list of failed fields.
- `scripts/build_stapel.py` — given a list of booking lines, produces a valid Buchungsstapel XML envelope.
- `scripts/fixture_generator.py` — generates deterministic test fixtures (valid + broken) for CI.

## Five eval prompts
1. "Build a Buchungsstapel for three bookings: EUR 1,200.00 net on account 4000 with tax key 19%, EUR 500.00 on account 4200 with tax key 7%, and EUR 100.00 on account 8000 with tax key 0%." → must produce a valid XML envelope with all mandatory header fields and all three booking lines.
2. "My validator reports 'Steuerschlüssel fehlt'. What does that mean and how do I fix it?" → must name "tax key missing", explain it is mandatory for every booking line, and give the fix (add the correct Steuerschlüssel for the account).
3. "Pin the EXTF schema version we use and show how a re-verification run would look." → must read config, never hardcode, and print a dated re-verification log entry.
4. "Generate test fixtures for our DATEV integration." → must produce a minimal valid Buchungsstapel plus a deliberately broken one for negative testing.
5. "Export our 2026 accounting data for the auditor in DATEV format." → must produce a complete, chronological, checksummed export with a manifest, not a raw DB dump.

## What this skill does better than generic agents
- It encodes the *DATEV-specific* EXTF structure (header + Buchungsstapel), not a generic XML format.
- It maps validation errors to specific fixes, because DATEV error codes are opaque without context.
- It pins the schema version in config and marks it "unverified until DATEV confirms", because DATEV does not publish a public version page.
- It generates deterministic test fixtures, which generic agents skip.
