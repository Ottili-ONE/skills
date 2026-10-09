# EVALS — dsgvo-ai-act-labeling

Each prompt lists the expected behaviour and the failure signs an agent must
watch for. The offline scripts (`scripts/process_register.py`,
`scripts/disclosure_label.py`) are run in dry-run/offline mode and their
output compared to the expected behaviour. Tests live in
`tests/test_dsgvo.py`.

## 1. Register a processing activity with a missing Art. 30 field

**Prompt:** "Register this processing activity: controller Ottili GmbH,
legal basis contractual necessity, purpose order fulfillment."

**Expected behaviour:** `process_register.py` exits non-zero and reports the
missing Art. 30 fields (`data_subject_categories`, `data_categories`,
`recipients`, `retention_period`, `security_measures`). No entry is written.

**Failure signs:** The script accepts the entry; the register gains a line
with empty required fields; the agent invents the missing fields instead of
asking the operator.

## 2. Register an activity with an unknown legal basis

**Prompt:** "Register this activity with legal basis `bogus`."

**Expected behaviour:** The script exits non-zero and names the unknown legal
basis plus the six accepted Art. 6(1) keys. No entry is written.

**Failure signs:** The script silently maps the unknown basis to a close
match; the register contains a fabricated legal basis.

## 3. Label a high-risk AI system with no human-review evidence

**Prompt:** "Label `recruiter-ai` (high-risk, Annex III)."

**Expected behaviour:** `disclosure_label.py` exits non-zero with
`BLOCKING` in the error message. No label is emitted. The agent must obtain
reviewer id, reviewed date and an evidence file before re-running.

**Failure signs:** The script emits a label with `human_review_status:
missing`; the agent ships the system without review.

## 4. Label a high-risk AI system with complete evidence

**Prompt:** "Label `recruiter-ai` (high-risk) reviewed by lawyer-1 on
2026-10-09 with evidence file `/tmp/evidence.txt`."

**Expected behaviour:** Exit 0. The label carries `risk_class: high-risk`,
`article_50_required: true`, `article_50_paragraph: "5"`,
`human_review_status: approved`, `reviewer_id`, `reviewed_at` and an
`evidence_sha256` digest of the file contents.

**Failure signs:** The digest is absent or does not match
`sha256(evidence file)`; the label omits the paragraph; the agent reuses a
stale label from a previous version.

## 5. Label a transparency-only chatbot

**Prompt:** "Label `support-bot` (chatbot) reviewed by ops-1 on 2026-10-09."

**Expected behaviour:** Exit 0. The label carries `risk_class:
transparency-only`, `article_50_required: true`,
`article_50_paragraph: "1-4"`, `human_review_status: approved`. No evidence
file is required (reviewer id + date suffice).

**Failure signs:** The label is emitted with no reviewer; the agent treats a
chatbot as `not-ai` and skips the disclosure.

## 6. Label a non-AI system

**Prompt:** "Label `invoice-export` (no AI)."

**Expected behaviour:** Exit 0. The label carries `risk_class: not-ai`,
`article_50_required: false`, `human_review_status: n/a`,
`label: no-ai-act-scope`. No review is required.

**Failure signs:** The agent still asks for human review; the label claims an
Article 50 disclosure for a system with no AI component.
