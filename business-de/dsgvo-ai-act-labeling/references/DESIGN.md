# DESIGN — dsgvo-ai-act-labeling

## Trigger description (draft for SKILL.md front matter)

> Use this skill when an Ottili agent must decide whether AI-generated
> content published on Ottili (or processed in Ottili) needs a GDPR processing
> register entry, a DPIA, or an EU AI Act Article 50 label — and when it must
> produce the human-review evidence that exempts it from labelling.
> Triggers: "do we need to label this AI-generated image", "is this text
> AI-generated", "update the processing register", "does this use case need
> a DPIA", "who is the editorial responsible person".

## What this skill does better than a generic agent

- **Decision cascade, not a vibe check**: classify the content first
  (synthetic / assist / augment / disclose), then test the Art. 50(4)
  exception with its two conjuncts, then decide label or no label.
- **Evidence-gated exception**: the human-review exemption is not "someone
  looked at it"; it needs a named natural person with editorial
  responsibility and a review record. The skill ships a template for that
  record.
- **Date-stamped applicability**: Art. 50 applies since 2026-08-02; the
  machine-readable marking duty for pre-2026-08-02 systems applies from
  2026-12-02. Both are pinned in `config/versions.json`, not hardcoded.
- **GDPR tie-in**: every AI use is also a processing activity; the skill
  produces the Art. 30 register row and the Art. 35 DPIA trigger checklist
  from the same classification.

## Procedure outline

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
   declaration (JSON-LD `contentRating`/`aiDisclosure` field, or the
   Art. 50(2) marking schema once pinned).
4. **GDPR side**: write the Art. 30 processing-register row (purpose, data
   categories, recipients, transfers, retention class from gobd-archive,
   safeguards). Run the Art. 35 DPIA trigger checklist; if any trigger fires,
   consult the DPO before launch.
5. **Re-verify dates** before any audit: re-fetch the Omnibus recital near
   2026-12-02.

## Scripts planned

| Script | Purpose |
|---|---|
| `scripts/classify_content.py` | Bucket a piece of content into synthetic/assist/augment/disclose from a metadata file; exits non-zero on ambiguous input. |
| `scripts/ai_label_check.py` | Applies the Art. 50(4) exception test to a review-record JSON; prints LABEL or EXEMPT with the failing conjunct. |
| `scripts/processing_register.py` | Emits an Art. 30 row from a use-case description + retention class; validates required fields. |

## Five eval prompts

1. **Synthetic image.** "Ottili publishes an AI-generated product photo with no
   human edit. Label?" → LABEL. Failure sign: publishing without a mark.
2. **Human-reviewed copy.** "An editor rewrote the AI draft and takes
   editorial responsibility. Label?" → EXEMPT, but only if the review record
   names the person. Failure sign: exempting on the strength of "someone
   reviewed it" with no record.
3. **Pre-2026-08-02 system.** "We placed an AI system on the market 2026-07-15.
   When is the machine-readable marking duty?" → 2026-12-02. Failure sign:
   applying it immediately.
4. **DPIA trigger.** "We score candidates with an AI model on special-category
   data." → DPIA mandatory, consult DPO. Failure sign: skipping the DPIA.
5. **Register gap.** "The processing register has no row for the AI content
   pipeline." → FAIL: add the row before publishing. Failure sign: publishing
   with an empty register.
