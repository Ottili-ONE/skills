# DESIGN — gobd-archive

## Trigger description (draft for SKILL.md front matter)

> Use this skill when an Ottili agent must store accounting documents, set up
> a retention policy, produce an audit export, or decide whether a document
> may be deleted, under German GoBD. Triggers: "set up the retention policy",
> "is this overwrite GoBD-compliant", "export 2026 accounting data for the
> auditor", "can we delete this 2018 invoice now".

## What this skill does better than a generic agent

- **Retention classes with the effective date**: 8y vouchers / 10y books /
  6y correspondence, all effective 2025-01-01 (BEG IV). The skill states the
  clock starts at year-end and gives the computed end date per year, so an
  agent never computes from the document's own date.
- **Immutability as a technical property**: append-only + hash-chaining +
  no in-place update, not a policy statement (per BDO guidance).
- **The 6-year class is not "all correspondence"**: three sub-types with
  traps (an email you only printed; a sent letter you cannot reproduce).
- **Purge is blocked unless both conditions hold**: retention end reached
  **and** no audit open. `scripts/purge_decision.py` exits non-zero when
  blocked, so it is safe to wire into a CI gate.
- **Audit export is a manifest-backed, chronological, checksummed artefact**,
  not a raw DB dump.

## Procedure outline

1. **Classify the document** — invoice (Buchungsbeleg), bookkeeping entry,
   annual account (Bilanz/GuV), commercial correspondence.
2. **Assign retention class** — vouchers 8y, books/annual accounts 10y,
   commercial correspondence 6y (BEG IV, effective 2025-01-01). Pin in config;
   let the tax advisor confirm.
3. **Enforce immutability** — append-only storage, hash-chained records, no
   in-place updates, no deletion before retention end.
4. **Write the Verfahrensdokumentation** — system, storage medium, retention
   periods, export format, access controls, backup procedure.
5. **Export for audit** — complete, chronological, checksummed export with a
   manifest.
6. **Verify on retention end** — confirm the purge is permitted, document the
   decision, keep the approval record for the full retention of the purge
   record itself.

## Scripts planned

| Script | Purpose |
|---|---|
| `scripts/retention_classify.py` | Classify a document and compute its retention end date. |
| `scripts/immutability_check.py` | Verify append-only + hash-chaining; fail on in-place update. **Read-only by default** (`--init-state`/`--write-state` opt-in). |
| `scripts/audit_export.py` | Produce a chronological, checksummed export with a manifest; `--verify` checks both directions. |
| `scripts/purge_decision.py` | Decide whether a purge is permitted; exit non-zero when blocked. Accepts `--today` for deterministic decisions. |

## Five eval prompts

1. **In-place overwrite.** "Our system overwrites invoices in place. Is that
   GoBD-compliant?" → No. Immutability is technical: append-only, hash-chained,
   no in-place update. Failure sign: calling it acceptable.
2. **Retention for a 2026 invoice.** "What retention period applies to a
   2026 invoice and when can we delete it?" → 8 years from year-end →
   2034-12-31. Failure sign: 7 years; computing from the invoice date.
3. **Verfahrensdokumentation.** "Write the checklist." → Six items: system,
   storage medium, retention periods, export format, access controls, backup
   procedure. Failure sign: missing access controls or backup procedure.
4. **Audit export.** "Export 2026 accounting data for the auditor." →
   Chronological, checksummed export with a manifest, not a raw DB dump.
   Failure sign: raw DB dump; no manifest.
5. **"10 years for everything".** "A colleague says retention is 10 years for
   everything. Who is right?" → Wrong for documents whose retention starts on/
   after 2025-01-01. 10y books, 8y vouchers, 6y correspondence. Failure sign:
   agreeing unconditionally; omitting the effective date.
