# Review record template — dsgvo-ai-act-labeling

Fill one per piece of AI-assisted content that relies on the Art. 50(4)
exception. Keep it for the full retention period (see `gobd-archive`).

```json
{
  "content_id": "...",
  "bucket": "assist|augment|synthetic|disclose",
  "reviewer": {"type": "natural_person", "name": "...", "role": "editor"},
  "reviewed_at": "2026-10-13T00:00:00Z",
  "editorial_responsibility": true,
  "art50_4_conjunct_a": true,
  "art50_4_conjunct_b": true,
  "exception_applies": true,
  "label_applied": false,
  "retention_class": "6y",
  "retention_end": "2032-12-31"
}
```

Both conjuncts must be `true` for `exception_applies` to be `true`.
