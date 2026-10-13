---
name: dsgvo-ai-act-labeling
description: "Decide whether AI-generated content published on Ottili needs a GDPR processing-register entry, a DPIA, or an EU AI Act Article 50 label — and produce the human-review evidence that exempts it from labelling. Use when an agent must classify AI content, update the processing register, trigger a DPIA, or name an editorial responsible person. Not for legal advice beyond these sources."
license: MIT-compat
compatibility: "framework-agnostic; GDPR Art. 5/6/30/35, EU AI Act Art. 50; offline validation"
metadata: {}
allowed-tools: []
---

# dsgvo-ai-act-labeling

## When to use this skill

Use this skill when an Ottili agent must decide whether AI-generated content
published on Ottili (or processed in Ottili) needs a GDPR processing register
entry, a DPIA, or an EU AI Act Article 50 label — and when it must produce
the human-review evidence that exempts it from labelling. Do **not** use it
for non-AI content, for legal advice beyond these sources, or for
third-country data transfers (see a separate Schrems II procedure).

## Description

Classify AI content into synthetic / assist / augment / disclose, run the
Art. 50(4) exception test with its two conjuncts, decide label or no label,
and emit the matching GDPR Art. 30 processing-register row and Art. 35 DPIA
trigger checklist. Art. 50 applies since 2026-08-02; the machine-readable
marking duty for pre-2026-08-02 systems applies from 2026-12-02. Both dates
are pinned in `config/versions.json`, never hardcoded.

## Procedure

1. **Classify the content** (one of four buckets):
   - `synthetic` — fully AI-generated, no human input (label).
   - `assist` — AI drafts, human publishes unchanged (label unless reviewed).
   - `augment` — AI modifies human content materially (label).
   - `disclose` — AI used only for spelling/translation (no label).
2. **Run the Art. 50(4) exception test**: (a) did a natural person review
   or exercise editorial control? (b) is that person named and accountable?
   Both must be true. Record the review in `references/review-record.md`.
3. **Decide the label**: if the exception fails, mark the content
   `#ai-generated` or an equivalent visible mark plus a machine-readable
   declaration. If it passes, no label — but keep the review record.
4. **GDPR side**: write the Art. 30 processing-register row (purpose, data
   categories, recipients, transfers, retention class from `gobd-archive`,
   safeguards). Run the Art. 35 DPIA trigger checklist; if any trigger fires,
   consult the DPO before launch.
5. **Re-verify dates** before any audit: re-fetch the Omnibus recital near
   2026-12-02.

## Decision tables

### Content classification

| Bucket | Definition | Label? |
|---|---|---|
| synthetic | fully AI-generated, no human input | yes |
| assist | AI drafts, published unchanged | yes, unless reviewed |
| augment | AI materially modifies human content | yes |
| disclose | AI for spelling/translation only | no |

### Art. 50(4) exception test

| Conjunct | Must be true? |
|---|---|
| A natural person reviewed or exercised editorial control | yes |
| That person is named and holds editorial responsibility | yes |

Both must be true. A missing review record fails the exception.

## Pitfalls from research

- **Art. 50 applies since 2026-08-02**, not when the system was placed on the
  market. The Digital Omnibus (Regulation (EU) 2026/1744) postponed Annex III
  high-risk dates but left Art. 50 unchanged.
- **The machine-readable marking duty for pre-2026-08-02 systems applies
  from 2026-12-02** — a secondary-source date; re-verify against the Omnibus
  recital before relying on it.
- **"Someone reviewed it" is not enough.** The exception needs a named natural
  person with editorial responsibility and a review record.
- **Every AI use is also a processing activity.** A missing Art. 30 row is a
  GDPR compliance gap, not a paperwork issue.
- S3 (DQS) and S4 (IHK München) phrase the exception slightly differently.
  The operative test is the conjunction in Art. 50(4). Have a lawyer confirm
  before a publication decision rests on this exception.

## Verification checklist

- [ ] Content classified into one of the four buckets
- [ ] Art. 50(4) exception test run; both conjuncts checked
- [ ] Review record names the person and the date
- [ ] Label applied (or exemption justified with evidence)
- [ ] Art. 30 processing-register row written with a retention class
- [ ] Art. 35 DPIA trigger checklist run; DPO consulted if any trigger fires
- [ ] Art. 50 applicability dates pinned from config, not hardcoded

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
- [Design](references/DESIGN.md)
- [Review record template](references/review-record.md)
