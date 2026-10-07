# DESIGN: gobd-archive
## Trigger description (SKILL.md description draft, <=1024 chars)
"Enforce GoBD-compliant document archiving for Ottili accounting flows: retention classes, immutability, Verfahrensdokumentation and tax-audit export. Use when an agent must classify a document for retention, decide whether an archive write is final, produce an audit export (Auskunftsverlangen), or check that a retention policy matches the BMF letter. Not for general file storage or non-German tax law."
## Procedure outline
1. **Classify the document** — invoice/voucher (Buchungsbeleg) -> 8 years; books/annual accounts/inventories -> 10 years; commercial correspondence -> 6 years. Retention starts at year-end (31.12. of the year the voucher was created). Re-verify against HGB §257/AO §147; treat as configurable policy with tax-advisor confirmation.
2. **Immutability gate** — writes append-only; no overwrite, no in-place edit, no delete before retention end. Every write records: SHA-256, timestamp (UTC, ISO 8601), actor, source system, retention class, retention end date.
3. **Verfahrensdokumentation** — record the procedure: input formats, conversion steps, storage medium, access controls, retention logic, export capability. This is the artefact auditors ask for; keep it versioned.
4. **Audit export** — on request produce: file list with checksums, retention dates, retrieval path, and a proof that originals are unchanged (re-hash on demand). IDW PS 880 defines the audit interface.
5. **Retention check** — scheduled scan: for each record, confirm file still parses, SHA-256 matches, retention end date computed correctly, and anything past retention end is scheduled for secure deletion (with a 30-day soft hold before irreversible deletion).
## Scripts planned
- `scripts/classify_document.py` — given document type + year, outputs retention class and end date.
- `scripts/retention_scan.py` — scans archive, verifies checksums, flags expired records, emits audit-export JSON.
- `scripts/verfahrensdokumentation.py` — renders the current policy as a one-page PDF/Markdown artefact.
## Five eval prompts
1. "Our archive stored a 2026 supplier invoice. When does the 8-year retention end?" -> 2034-12-31 (year-end rule), and the agent must state the rule, not guess.
2. "Can we edit an archived invoice to correct a typo?" -> No: immutability; create a correction voucher with a reference to the original and record both.
3. "An auditor asks for the Verfahrensdokumentation. What do we hand over?" -> the versioned procedure artefact covering input formats, conversion, storage, access, retention, export.
4. "Run the retention scan on our sample archive." -> must report per-record status (OK/expired/corrupt) and a machine-readable summary.
5. "A record is past retention end. Can we delete it now?" -> No: 30-day soft hold, then secure deletion, logged.
## What this skill does better than generic agents
- Encodes the retention-class decision table with the year-end start rule, which generic agents get wrong.
- Treats immutability as a gate with a recorded checksum, not a folder permission.
- Produces the audit export artefact explicitly (IDW PS 880), which generic agents skip.
