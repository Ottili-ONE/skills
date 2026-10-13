# EVALS — dsgvo-ai-act-labeling

Each prompt lists the expected behaviour and the failure signs an agent must
watch for.

## 1. Synthetic image
**Prompt:** "Ottili publishes an AI-generated product photo with no human
edit. Label?"

**Expected behaviour:** LABEL. Bucket `synthetic`; the Art. 50(4) exception
cannot apply because no human reviewed it. Mark `#ai-generated` plus a
machine-readable declaration.

**Failure signs:** Publishing without a mark; claiming the exception on the
strength of "it is obviously a product photo".

## 2. Human-reviewed copy
**Prompt:** "An editor rewrote the AI draft and takes editorial
responsibility. Label?"

**Expected behaviour:** EXEMPT — but only if the review record names the
person. Run `scripts/ai_label_check.py` against the record; both conjuncts
must be true.

**Failure signs:** Exempting on the strength of "someone reviewed it" with no
record; exempting when the reviewer is not named.

## 3. Pre-2026-08-02 system
**Prompt:** "We placed an AI system on the market 2026-07-15. When is the
machine-readable marking duty?"

**Expected behaviour:** 2026-12-02 (Art. 50(2), per the Digital Omnibus).
Art. 50 itself applies since 2026-08-02. Read both dates from
`config/versions.json`.

**Failure signs:** Applying the marking duty immediately; treating 2026-08-02
as the marking date.

## 4. DPIA trigger
**Prompt:** "We score candidates with an AI model on special-category data."

**Expected behaviour:** DPIA mandatory (Art. 35). Consult the DPO before
launch. The Art. 30 register row must also be written.

**Failure signs:** Skipping the DPIA; writing the register row but not
running the DPIA checklist.

## 5. Register gap
**Prompt:** "The processing register has no row for the AI content pipeline."

**Expected behaviour:** FAIL — add the row before publishing. Every AI use is
a processing activity; an empty register is a GDPR compliance gap.

**Failure signs:** Publishing with an empty register; treating the register
as optional paperwork.

## Near-miss triggers

### N1. "It is just a spelling checker, so no label"
**Trap:** the `disclose` bucket (spelling/translation only) is genuinely
exempt, but only if the AI made no material change. If the AI rewrote the
text, it is `assist` or `augment`.

### N2. "The marketing team reviewed it"
**Trap:** the exception needs a **named natural person** with editorial
responsibility and a review record. A team review with no named individual
fails conjunct (b).

### N3. "Art. 50 does not apply until 2027"
**Trap:** Art. 50 applies since 2026-08-02 (confirmed by three 200-OK
sources on 2026-10-13). The 2027 date is the Annex III high-risk obligation,
which the Digital Omnibus postponed.
