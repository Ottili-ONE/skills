# DESIGN: dsgvo-ai-act-labeling

## Trigger description (SKILL.md description draft, <=1024 chars)
"Apply GDPR workflows and EU AI Act Article 50 disclosure decisions for Ottili flows: processing-register entries, human-review evidence and AI-system labeling. Use when an agent must classify a data-processing activity under GDPR, decide whether an AI system needs an Article 50 disclosure with human-review evidence, or update the processing register. Not for general privacy policy text, non-EU AI systems, or DSGVO member-state additions beyond the EU baseline."

## Procedure outline
1. **Classify the processing activity** — identify data subjects, purpose, legal basis (Art. 6 GDPR) and whether personal data is involved. No personal data => skip GDPR; personal data => continue.
2. **Register in the processing register (Art. 30 GDPR)** — controller name, purpose, categories of data subjects/data, recipients, retention period, security measures. Update on every change; keep current.
3. **Check AI Act scope** — does the system use AI? Is it high-risk? High-risk => Article 50 disclosure with human-review evidence required before deployment. Not high-risk => no Article 50 label needed, but still document the decision.
4. **Human-review evidence** — record who reviewed what and when. Evidence kept per the retention class inherited from `gobd-archive` (business records under HGB/AO). Review must be meaningful, not a checkbox.
5. **Label** — emit a machine-readable label: system name, risk class, Art. 6/Art. 50 status, human-review status, date of last review. Store alongside the system artefact; re-verify on every release cycle. Never auto-approve high-risk without human review. Log every label decision with timestamp and reviewer id. Treat missing evidence as blocking until resolved. Re-run classification on material change to system inputs/outputs. Never reuse a stale label across versions without re-verification. Store labels tamper-evidently (checksums) and coordinate with `gobd-archive` for retention of label artefacts.

## Scripts (built 2026-10-13, names differ slightly from this draft)
- `scripts/disclosure_label.py` — the Art. 50 disclosure decision (four-gate tree: AI? high-risk? transparency-only?) emitting a machine-readable label with human-review evidence status. Missing evidence for a high-risk system is BLOCKING.
- `scripts/process_register.py` — appends an Art. 30 GDPR processing-register entry from a machine-readable activity template; append-only, enforces the 7 Art. 30(1) mandatory fields.
- `scripts/label_check.py` — verifies a label artefact before an agent relies on it: required fields present, high-risk systems must have approved human review, review date inside the re-verification window, checksum matches the artefact content (tamper evidence).

## Five eval prompts (re-verified 2026-10-13)
1. "Classify this flow: we log IP addresses of visitors for analytics." -> must say personal data = yes (GDPR applies), propose an Art. 6 basis, and flag that IP logging needs a lawful basis.
2. "Is our chatbot high-risk under the EU AI Act?" -> must run the scope check: if it does not interact with natural persons in a way listed in Art. 5(1) annex, say not high-risk and document; if it does, require Article 50 disclosure.
3. "Someone approved the AI label with a rubber-stamp review last month." -> must flag missing/insufficient human-review evidence as blocking and require a dated, named review.
4. "Re-verify this system's label after we changed the input data source." -> must re-run classification, detect the material change, and refuse to reuse the stale label.
5. "Where do we keep the label artefact and for how long?" -> must store it tamper-evidently alongside the system artefact and defer retention timing to `gobd-archive` (GoBD retention classes), not invent a separate clock.

## What this skill does better than generic agents
- It encodes the *legal* trigger (GDPR Art. 6/30 + AI Act Art. 50) instead of "be careful with privacy".
- It separates "no personal data => skip" from "personal data => register", which generic agents conflate.
- It defers retention to `gobd-archive` so the two skills agree on one clock instead of two.
- It treats missing human-review evidence as a *blocking* failure, not a warning.
