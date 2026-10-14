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
A complete entry always carries a `recorded_at` timestamp (the script sets
it from the current date, never from the caller) so the register is valid
GoBD evidence.

**Failure signs:** The script accepts the entry; the register gains a line
with empty required fields; the agent invents the missing fields instead of
asking the operator; an entry with `recorded_at: null`.

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

## 7. Register an activity where the controller changes mid-cycle

**Prompt:** "Register an activity where the controller changes mid-cycle."

**Expected behaviour:** Never edit the existing entry in place — that breaks
GoBD immutability. Append a new entry with a fresh `recorded_at` and a note
that points at the superseded entry id. The register stays a valid append-only
JSONL log; a reader can trace the full history of one activity.

**Failure signs:** Mutating an entry in place; losing the superseded entry;
writing a register with fewer lines than recorded activities.

## 8. Label a general-AI system (not transparency-only, not high-risk)

**Prompt:** "Label `report-ml` (general AI, no transparency obligation)."

**Expected behaviour:** Exit 0. The label carries `risk_class: general`,
`article_50_required: false`, `article_95_documented: true` and
`human_review_status: not-required`. No Article 50 disclosure is emitted and
no human review is needed — the decision is documented, not disclosed.

**Failure signs:** Emitting an Article 50 disclosure for a general system;
asking for human review on a system that does not need it; classifying a
general system as high-risk.

## Near-miss triggers

Prompts that look fine at first glance but hide a trap. The agent must catch
the trap and still produce a passing artefact.

### N1. "We anonymised the data, so no legal basis is needed"
**Trap:** anonymisation is itself a processing activity that needs a legal
basis and a register entry. Anonymisation does not remove the original
collection's basis either — it chains. Record the anonymisation as a new
activity that points at the source entry.

### N2. "The chatbot only answers FAQs, so it is transparency-only"
**Trap:** a chatbot that generates text can be high-risk if it makes a
decision affecting a person. The rule is not the *feature* (FAQ) but the
*impact* (legal effect / significant decision). A general-AI system behind
the chatbot also triggers Art. 95 documentation, which the
transparency-only label omits.

### N3. "Article 50 disclosure is a one-off"
**Trap:** the disclosure is a living artefact. When the system changes, the
label must be re-issued and the old one kept (GoBD). Never edit in place.

### N4. "The human reviewer signed off, so the evidence is complete"
**Trap:** the evidence record needs a date, a reviewer id, a scope and a
re-review date. A bare signature is `human_review_incomplete` — the
`disclosure_label.py` checker rejects it.

### N5. "GDPR only applies to EU customers"
**Trap:** Art. 3 GDPR applies to any offer of goods/services to people in
the EU, not only customers. B2B newsletter recipients in the EU are still
data subjects. The register entry must cover the offer, not the contract.


---

## Run these checks

Every prompt above names a script and an expected exit code. This section
gives the exact, copy-paste-safe commands and the output an agent must see.
All commands are run from the skill directory
(`cd skills/business-de/dsgvo-ai-act-labeling`). The register is append-only:
never edit an entry in place (GoBD immutability; see `gobd-archive`).

```bash
# 1. incomplete Art. 30 entry -> exit 1, no entry written
python3 scripts/process_register.py --activity act_incomplete.json --register out.jsonl
# Art. 30 entry missing fields: ['data_subject_categories', 'data_categories',
#                                'recipients', 'retention_period', 'security_measures']

# 2. complete entry, human-readable basis -> exit 0
python3 scripts/process_register.py --activity act_complete.json --register out.jsonl
# {"ok": true, "entry": {... "legal_basis": "art6_1b_contract", "recorded_at": "2026-10-14"}}

# 2b. unknown legal basis -> exit 1
python3 scripts/process_register.py --activity act_bad.json --register out.jsonl
# unknown legal basis 'bogus'; choose from ['art6_1a_consent', ...]

# 3. high-risk system, NO human-review evidence -> exit 1 (BLOCKING)
python3 scripts/disclosure_label.py --system sys_hr_noev.json
# high-risk system 'recruiter-ai' BLOCKING: human-review evidence missing

# 4. high-risk system WITH evidence -> exit 0
python3 scripts/disclosure_label.py --system sys_hr.json --evidence evidence.txt
# {"risk_class": "high-risk", "article_50_paragraph": "5",
#  "human_review_status": "approved", "evidence_sha256": "58f2...0c54"}

# 5. transparency-only chatbot -> exit 0, no evidence file required
python3 scripts/disclosure_label.py --system sys_cb.json
# {"risk_class": "transparency-only", "article_50_paragraph": "1-4",
#  "human_review_status": "approved"}

# 6. non-AI system -> exit 0, no review required
python3 scripts/disclosure_label.py --system sys_na.json
# {"risk_class": "not-ai", "article_50_required": false,
#  "human_review_status": "n/a", "label": "no-ai-act-scope"}

# 8. general AI -> exit 0, documented, not disclosed
python3 scripts/disclosure_label.py --system sys_gen.json
# {"risk_class": "general", "article_50_required": false,
#  "article_95_documented": true, "human_review_status": "not-required"}
```

The human-readable synonyms (`contractual necessity`, `legitimate
interests`, ...) are accepted on input; the register always stores the
canonical Art. 6(1) key so the artefact is machine-checkable. Verified
2026-10-14 against `eur-lex.europa.eu/eli/reg/2024/1689/oj` (HTTP 202; the
legal-content HTML body was empty for curl, so the Art. 50 enforcement
calendar remains **unverified** — a lawyer must confirm).
