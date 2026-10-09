---
name: webhooks-safe
description: "Ingest inbound webhooks safely for Ottili flows: verify HMAC signatures over the raw body, dedupe by event id with a TTL, preserve per-stream order, respect provider replay windows, route persistent failures to a dead-letter queue, and validate outbound delivery targets against an allow-list to prevent SSRF. Use when an agent must receive, verify or process a webhook payload; when a webhook arrives out of order or twice; or when a webhook handler fails. Not for outbound retry engineering."
license: MIT-compat
compatibility: "framework-agnostic; HMAC-SHA256 webhook verification; offline validation"
metadata: {}
allowed-tools: []
---

# webhooks-safe

## When to use this skill

Use this skill when an agent must ingest an inbound webhook for Ottili
flows: verify its signature over the raw body, dedupe it by event id,
preserve delivery order within a stream, respect the provider's replay
window, route persistent failures to a dead-letter queue, and — if the
skill ever needs to deliver outbound — do so only against an allow-listed
Ottili endpoint. Do **not** use it for outbound retry engineering (that
lives in the engineering playbooks) or for providers whose signature scheme
is unknown.

## Procedure (numbered, in order)

1. **Verify the signature over the raw body.** Recompute the HMAC with the
   provider's secret. Reject if it does not match. Never trust headers alone,
   never parse-then-re-encode the body, and always use
   `hmac.compare_digest` (a plain `==` is a timing attack).
2. **Dedupe.** Every webhook carries an event id; store the id with a TTL; on
   a duplicate id, ack and skip. Never process twice. Check-and-set must be
   atomic.
3. **Preserve order.** Within a single delivery stream, process events in
   arrival order; if an event is out of sequence, hold it until the missing
   event arrives or the replay window expires. Ordering is per stream, never
   global.
4. **Respect replay windows.** If a provider guarantees delivery within N
   minutes, hold unprocessed events for that window before declaring them
   lost. For Stripe the timestamp is part of the signature — reject stale
   signatures before checking the HMAC.
5. **Dead-letter.** On persistent failure (3 attempts), move the event to the
   dead-letter queue with the raw payload and the failure reason; never
   silently drop.
6. **SSRF-safe delivery.** Validate the target URL against the allow-list of
   Ottili endpoints; reject IP literals and `localhost` (never resolve them).
7. **Log.** Record every verify/dedupe/delivery decision with the event id.

## Decision tables

### Provider signature schemes

| Provider | Header | Algorithm | Replay window |
|---|---|---|---|
| GitHub | `X-Hub-Signature-256` | HMAC-SHA256, `sha256=<hex>` | 24h TTL on event id |
| Stripe | `Stripe-Signature` | HMAC-SHA256, `t=<ts>,v1=<hex>` | 5 minutes |
| PayPal | `X-PayPal-Signature` | HMAC-SHA256 (unverified) | provider-defined |
| Twilio | `X-Twilio-Signature` | HMAC-SHA256 over URL + body (unverified) | provider-defined |

### Dedupe outcome

| Situation | Action |
|---|---|
| Event id seen, within TTL | Ack and skip; never process twice |
| Event id seen, TTL expired | Re-process (idempotency must still hold) |
| Event id new | Process and store with TTL |

### Dead-letter trigger

| Trigger | Action |
|---|---|
| Signature invalid | Reject immediately; do not dead-letter (it is not our event) |
| Processing throws 3 times | Move to dead-letter with raw payload + reason |
| Replay window expired | Move to dead-letter marked "lost" |

### Outbound allow-list check

| Target | Action |
|---|---|
| Allow-listed Ottili host + path | Deliver |
| Allow-listed host, different path | Reject (path not allowed) |
| Any other host | Reject immediately (SSRF) |
| IP literal or `localhost` | Reject (never resolve) |

## Pitfalls from research

- **Verify over the raw body, not the parsed body.** Re-encoding the JSON
  changes byte order and every signature fails. Read the raw bytes.
- **Stripe's timestamp is part of the signature.** A signature older than the
  replay window is a replay attack — reject it before checking the HMAC.
- **GitHub's `X-Hub-Signature-256` is `sha256=<hex>`.** The older
  `X-Hub-Signature` (SHA1) is deprecated; never fall back to it.
- **Dedupe must be atomic.** Check-and-set on the event id must be one
  operation; a race processes the event twice.
- **Never deliver to arbitrary hosts.** An attacker-controlled webhook payload
  that triggers an outbound call is an SSRF. Validate the target against the
  allow-list.
- **Ordering is per delivery stream, not global.** Two independent providers
  can interleave; only enforce order within one stream.
- **PayPal and Twilio schemes are unverified** until their docs are fetched
  at build time; the scripts fall back to plain HMAC-SHA256 and the skill
  flags the result as unverified.

## Verification checklist

- [ ] Signature verified over the raw body; reject on mismatch
- [ ] Stripe timestamp within replay window before HMAC check
- [ ] Event id stored with TTL; duplicates acked and skipped
- [ ] Out-of-sequence events held until missing event or replay window expires
- [ ] Persistent failures moved to dead-letter with raw payload and reason
- [ ] Outbound delivery target validated against the allow-list
- [ ] Every decision logged with the event id

## Near-miss triggers (stop and re-read)

- "I'll parse the JSON and verify against that" → raw bytes only.
- "The signature is old, but it's probably fine" → replay window first.
- "I'll just deliver to whatever URL is in the payload" → SSRF; allow-list it.
- "PayPal/Twilio use the same scheme as GitHub" → unverified; flag it.

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
- [Scripts](scripts/)
