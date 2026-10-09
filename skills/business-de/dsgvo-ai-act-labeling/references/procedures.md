# Procedures — dsgvo-ai-act-labeling

All versions are read from `config/versions.json` (never hardcode). GDPR is
stable but member-state implementations and EU AI Act implementing acts may
change; re-check EUR-Lex before each build and record the retrieval date in
`references/SOURCES.md`.

## 1. Classify the processing activity

Run the GDPR gate first. If the activity involves no personal data, the
processing register entry is optional — record it anyway for traceability and
mark `personal_data: false`.

Required Art. 30(1) fields, any missing field blocks the entry:

| Field | Example |
|---|---|
| `controller` | "Ottili GmbH" |
| `purpose` | "order fulfillment" |
| `data_subject_categories` | ["customers", "employees"] |
| `data_categories` | ["name", "address", "email"] |
| `recipients` | ["carrier", "payment provider"] |
| `retention_period` | "10y" |
| `security_measures` | "TLS 1.3, encryption at rest" |

Legal basis (Art. 6(1)) — exactly one primary basis per activity. The script
rejects unknown bases; do not invent synonyms.

## 2. Maintain the processing register

The register is a JSONL file, append-only. Never edit an existing entry in
place — that breaks GoBD immutability. On a change, append a new entry with
the new `recorded_at` and a note pointing at the superseded entry id.

```bash
python3 scripts/process_register.py --activity activity.json --register register.jsonl
```

**Good output** (append):
```json
{"ok": true, "entry": {"personal_data": true, "legal_basis": "art6_1b_contract", ...}, "register": "register.jsonl"}
```

**Bad output** — editing an entry in place:
```json
{"ok": true, "entry": {...}, "register": "register.jsonl", "note": "mutated entry 3"}
```
Detect it: the register file has fewer lines than the number of recorded
activities, or an entry lacks `recorded_at`.

## 3. Run the AI Act gate

Four gates, in order. A gate may short-circuit:

1. **AI at all?** `ai_type == "none"` => `not-ai`, no Art. 50, no review.
2. **Transparency-only?** `ai_type` in {chatbot, emotion-recognition,
   deep-fake, biometric-categorization} => Art. 50(1)-(4) disclosure. Human
   review required (reviewer id + date); evidence path optional but recorded.
3. **High-risk?** `ai_type` in {high-risk, "Annex III high-risk (Art. 6)"} =>
   Art. 50(5). Human review mandatory with an evidence **file**; the script
   hashes it (`sha256`) and the digest is part of the label. Missing file =>
   BLOCKING, never auto-approve.
4. **General AI** => Art. 95, no disclosure, but document the decision.

## 4. Human-review evidence

- Record `reviewer_id`, `reviewed_at` (ISO-8601) and `evidence_path`.
- The evidence file must exist at label time; the script refuses otherwise.
- Keep evidence for at least 10 years or per the retention policy — inherit
  the GoBD retention class from the `gobd-archive` skill (label artefacts are
  business records under HGB/AO).
- A review must be meaningful: it names the system, the risk class and the
  mitigations checked. A checkbox with no content is treated as missing.

## 5. Emit and store the label

```bash
python3 scripts/disclosure_label.py --system system.json
```

**Good output** (high-risk, approved):
```json
{
  "system": "recruiter-ai",
  "risk_class": "high-risk",
  "article_50_required": true,
  "article_50_paragraph": "5",
  "human_review_status": "approved",
  "reviewer_id": "lawyer-1",
  "reviewed_at": "2026-10-09",
  "evidence_sha256": "9f86d081...",
  "label": "article-50-disclosure-hr"
}
```

**Bad output** — a label reused across versions:
```json
{"system": "recruiter-ai", "risk_class": "high-risk", "label": "article-50-disclosure-hr", "reviewed_at": "2026-09-01"}
```
Detect it: `reviewed_at` predates the last release of the system artefact.

Store the label alongside the system artefact. Re-run classification on every
material change to inputs or outputs and on every release cycle. Treat
member-state additions (BDSG, French/ Dutch implementations) as unverified
until local counsel confirms.
