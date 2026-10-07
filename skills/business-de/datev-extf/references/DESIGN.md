# DESIGN: datev-extf

## Trigger description (SKILL.md description draft, <=1024 chars)
"Generate and validate DATEV EXTF (Exchange Format) posting stacks for Ottili accounting integrations: EXTF header fields, Buchungsstapel semantics, Datenservices contracts and validation errors. Use when an agent must emit, import, reconcile or debug a DATEV EXTF export; when a posting stack fails validation; or when mapping Ottili journal lines onto the DATEV contract. Not for general accounting logic or non-DATEV systems."

## Procedure outline
1. **Identify the context** — is this an export FROM Ottili to DATEV, or an import FROM DATEV to Ottili? The direction changes which fields are mandatory.
2. **Pin the EXTF version** — DATEV does not publish a public version page; pin the version the integrator/DATEV partner confirms and mark "unverified until DATEV confirms" (R3 rule: never hardcode).
3. **Emit the header** — Buchungsstapel header (Kopfdaten): Mandant, Buchungsdatum, Buchungstext, Schluessel, etc. Validate every field against the EXTF field catalogue.
4. **Emit the positions** — one row per position with the same keying rules; preserve order; never split a single journal line across two positions.
5. **Run validation** — DATEV validation errors are numeric codes; map each code to a fix. Treat every error as blocking.
6. **Reconcile** — compare Ottili journal hash against DATEV import acknowledgement; on mismatch, re-run with the pinned version and log the delta.

## Scripts planned
- `scripts/extf_emit.py` — emits a DATEV EXTF posting stack from Ottili journal lines.
- `scripts/extf_validate.py` — validates an EXTF file against the pinned field catalogue; emits machine-readable pass/fail with error codes.
- `scripts/extf_reconcile.py` — compares Ottili journal hash with DATEV acknowledgement; reports unknown-result deltas.

## Five eval prompts
1. "Emit a DATEV EXTF posting stack for a domestic purchase, EUR 500 net, 19% VAT." -> must produce the header + positions with the correct Buchungsschluessel and tax key.
2. "DATEV validation returns error code 1001. What does it mean?" -> must name the field and the fix (per the pinned catalogue).
3. "Pin the EXTF version we use." -> must read config, never hardcode, and mark unverified until DATEV confirms.
4. "Reconcile this Ottili journal with the DATEV acknowledgement." -> must compare hashes and report match/mismatch with the delta.
5. "Is a single journal line allowed to span two positions?" -> must say no and explain the one-row-per-position rule.

## What this skill does better than generic agents
- Encodes the EXTF field catalogue as a decision table instead of relying on memory.
- Pins the EXTF version and marks it unverified, because DATEV does not publish a version page.
- Treats the Ottili<->DATEV hash reconciliation as a first-class step, which generic agents skip.
