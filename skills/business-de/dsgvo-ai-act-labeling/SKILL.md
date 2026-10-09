---
name: dsgvo-ai-act-labeling
description: "Apply GDPR workflows and EU AI Act Article 50 disclosure decisions for Ottili flows: processing register entries, human-review evidence and AI labeling. Use when an agent must classify a data processing activity under GDPR, decide whether an AI system requires an Article 50 disclosure with human-review evidence, or update the processing register. Not for general privacy policy or non-EU AI systems."
license: MIT-compat
compatibility: "framework-agnostic; GDPR Art. 30/6, EU AI Act Art. 50; offline validation"
metadata: {}
allowed-tools: []
---

# dsgvo-ai-act-labeling

## When to use this skill

Use this skill when an agent must classify a data processing activity under
GDPR, decide whether an AI system needs an EU AI Act Article 50 disclosure
with human-review evidence, or maintain the GDPR processing register for
Ottili flows. Do **not** use it for general privacy policy text, non-EU AI
systems, or member-state-specific law beyond the EU baseline.

## Procedure

1. **Classify the processing activity.** Identify the data subject, purpose,
   legal basis (Art. 6 GDPR) and whether personal data is involved. If no
   personal data => skip the GDPR gate; if personal data => continue.
2. **Register in the processing register.** Record controller, purpose,
   categories of data subjects/data, recipients, retention period and
   security measures (Art. 30 GDPR). Append-only; never edit in place.
3. **Check AI Act scope.** Does the system use AI? Is it high-risk? If yes =>
   Article 50 disclosure with human-review evidence required before
   deployment. If no => no Article 50 label needed (but still document).
4. **Human-review evidence.** Record who reviewed what and when. Review must
   be meaningful, not a checkbox. Missing evidence for a high-risk system is
   BLOCKING.
5. **Label.** Emit a machine-readable label with system name, risk class,
   Article 50 paragraph, human-review status, date of last review. Re-verify
   on every release cycle; never reuse a stale label across versions.

## Decision tables

### AI Act risk classes

| ai_type | Risk class | Art. 50 | Human review |
|---|---|---|---|
| `none` | not-ai | not required | n/a |
| `chatbot`, `emotion-recognition`, `deep-fake`, `biometric-categorization` | transparency-only | 50(1)-(4) | required |
| `high-risk` / Annex III (Art. 6) | high-risk | 50(5) | required, evidence file mandatory |
| anything else | general | not required | not required |

### GDPR legal bases (Art. 6(1))

| Key | Label |
|---|---|
| `art6_1a_consent` | Consent (Art. 6(1)(a)) |
| `art6_1b_contract` | Contractual necessity (Art. 6(1)(b)) |
| `art6_1c_legal` | Legal obligation (Art. 6(1)(c)) |
| `art6_1d_vital` | Vital interests (Art. 6(1)(d)) |
| `art6_1e_task` | Public task (Art. 6(1)(e)) |
| `art6_1f_legit` | Legitimate interests (Art. 6(1)(f)) |

## Pitfalls from research

- **Never auto-approve high-risk.** A missing evidence file blocks the label;
  the script raises and the agent must not bypass it.
- **Transparency-only systems still need human review.** A chatbot label with
  no reviewer is rejected, not warned.
- **Re-run classification on material change.** A label emitted for v1 is not
  valid for v2; re-verify on every release cycle.
- **Inherit GoBD retention from `gobd-archive`.** Label artefacts are business
  records under HGB/AO; coordinate retention timing with that skill.
- **Member-state additions are unverified.** Germany (BDSG), France and the
  Netherlands may add requirements beyond the EU baseline; flag them until
  local counsel confirms.

## Verification checklist

- [ ] Processing activity classified; personal data present or not
- [ ] Art. 30 entry complete; legal basis valid
- [ ] Register is append-only; never edited in place
- [ ] AI Act gate run; risk class determined
- [ ] High-risk label has reviewer, date and evidence file with checksum
- [ ] Transparency label has reviewer and date
- [ ] Label re-verified on release change; no stale reuse
- [ ] Retention inherited from gobd-archive

## Near-miss triggers (stop and re-read)

- "I'll auto-approve this high-risk label" → BLOCKING; evidence file required.
- "A chatbot doesn't need a reviewer" → transparency-only still requires one.
- "The label from v1 is still valid" → re-run on every release cycle.
- "BDSG doesn't apply to us" → member-state additions are unverified until
  local counsel confirms.

## References

- [Procedures, worked examples and AI Act summaries](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
- [Scripts](scripts/)
