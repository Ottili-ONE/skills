# Procedures — dsgvo-ai-act-labeling

All dates are read from `config/versions.json`; never hardcode.

## 1. Classify the content

| Input | Bucket | Label? |
|---|---|---|
| fully AI-generated, no human input | synthetic | yes |
| AI drafts, published unchanged | assist | yes, unless reviewed |
| AI materially modifies human content | augment | yes |
| AI for spelling/translation only | disclose | no |

## 2. Art. 50(4) exception test

Both must be true:
- (a) a natural person reviewed or exercised editorial control
- (b) that person is named and holds editorial responsibility

Record the review in `references/review-record.md`.

## 3. Decide the label

If the exception fails: mark the content `#ai-generated` (visible) plus a
machine-readable declaration. If it passes: no label, but keep the review
record.

## 4. GDPR side

- Art. 30 processing-register row: purpose, data categories, recipients,
  transfers, retention class from `gobd-archive`, safeguards.
- Art. 35 DPIA trigger checklist: special-category data, systematic
  profiling, large-scale processing, automated decisions affecting
  individuals. If any trigger fires, consult the DPO before launch.

## 5. Re-verify dates

Art. 50 applies since 2026-08-02. The machine-readable marking duty for
pre-2026-08-02 systems applies from 2026-12-02 (secondary source; re-verify
against the Omnibus recital).

## Worked examples

### Good — human-reviewed assist content

```
bucket: assist
reviewer: {name: "Anna M.", role: "editor", reviewed_at: "2026-10-12"}
editorial_responsibility: true
=> exception_applies: true, label_applied: false
```

### Bad — no named reviewer

```
bucket: assist
reviewer: null
=> exception_applies: false, label_applied: true
```
