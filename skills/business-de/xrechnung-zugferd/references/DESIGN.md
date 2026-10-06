# DESIGN: xrechnung-zugferd

## Trigger description (SKILL.md description draft, ≤1024 chars)
"Generate, validate and archive German e-invoices (XRechnung / ZUGFeRD / Factur-X) compliant with EN 16931 and the UStG e-invoicing obligation (§14 UStG). Use when an agent must create, check, receive, convert or store e-invoices for B2B/B2G flows, decide whether a document is a valid e-invoice, pick the right profile, or set up a GoBD-compliant retention pipeline. Not for PDF-only invoices or non-German jurisdictions."

## Procedure outline
1. **Classify the document** — XML-only (XRechnung), hybrid PDF/A-3+XML (ZUGFeRD/Factur-X) or other. Reject paper/PDF-only as "sonstige Rechnung".
2. **Pin versions** — read pinned spec+validator versions from `config/versions.json` (never hardcode). Re-verify on a scheduled cadence; record in SOURCES.md.
3. **Choose the profile** — MINIMUM / BASIC WL / BASIC / EN 16931 (COMFORT) / EXTENDED. Default for B2B: EN 16931/COMFORT. EXTENDED only when sector extensions are required.
4. **Validate** — run KoSIT validator (or the pure-PHP `john-wink/en16931-php` fallback) against the pinned configuration. Treat every error as blocking; warnings must be documented.
5. **Check business rules** — mandatory BT-* fields, Leitweg-ID in BT-10, payment terms syntax in BT-20, tax split per rate.
6. **Archive** — keep the original file (XML or PDF-with-embedded-XML) unchanged; 8-year retention from year-end; record checksum, retrieval path and export test in the retention log.
7. **Re-verify** — on any spec/validator bump, re-validate the whole archive sample; log the run.

## Scripts planned
- `scripts/validate_invoice.py` — wrapper around the KoSIT validator or the PHP fallback; emits a machine-readable pass/fail JSON plus the list of failed rule IDs.
- `scripts/profile_selector.py` — given a context (B2B/B2G, data available, recipient capability) outputs the recommended profile and the missing fields.
- `scripts/retention_check.py` — scans the archive, verifies each file still parses, recomputes the SHA-256 and confirms the retention end date.

## Five eval prompts
1. "Our supplier sent a PDF invoice with no XML. Is it an e-invoice under German law, and what do we do?" → must say no, classify as sonstige Rechnung, and list the 2025-2028 transitional options.
2. "Generate a ZUGFeRD invoice for a domestic B2B sale, EUR 1,200.00 net, 19% VAT, buyer has a Leitweg-ID." → must produce a Factur-X/COMFORT document with BT-10 populated and a validation report.
3. "My validator reports rule BT-14 missing. What is BT-14 and how do I fix it?" → must name "Invoice issue date", explain it is mandatory in all profiles, and give the fix.
4. "Pin the XRechnung spec version we use and show how a re-verification run would look." → must read config, never hardcode, and print a dated re-verification log entry.
5. "Archive this invoice: which file do we keep and until when?" → must keep the original (XML or PDF/A-3 with embedded XML), not a print-to-PDF copy, and compute retention until 2034 for a 2026 invoice.

## What this skill does better than generic agents
- It encodes the *legal* trigger (§14 UStG + BMF letters) not just "validate XML".
- It distinguishes the five ZUGFeRD profiles with a decision table instead of guessing.
- It pins versions in config and mandates re-verification, because the standard moves twice a year.
- It treats the archive copy as a first-class artefact (checksum + export test), which generic agents skip.
