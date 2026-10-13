---
name: webhooks-safe
description: "Receive, verify, deduplicate and safely forward inbound webhooks (Meta, GitHub, Stripe, Twilio, DHL, or any HTTPS webhook) and forward payloads to a URL of your own choosing without enabling SSRF. Use when an agent must set up a webhook endpoint, verify a signature, stop replaying events, or deliver to a self-chosen URL."
license: MIT-compat
compatibility: "framework-agnostic; HMAC-SHA256, OAuth2; offline validation"
metadata: {}
allowed-tools: []
---

# webhooks-safe

## When to use this skill

Use this skill when an Ottili agent must **receive, verify, deduplicate and
safely forward** an inbound webhook (Meta/Facebook, GitHub, Stripe, Twilio,
DHL, or any HTTPS webhook) — or when it must **forward a payload to a URL of
its own choosing** without enabling SSRF. Do **not** use it for outbound
publishing (see `publish-reconcile-wp-meta`) or for polling APIs.

## Description

Verify inbound webhook signatures per provider, enforce at-most-once
processing keyed by a provider-defined event id, tolerate out-of-order
delivery, move repeated failures to a dead-letter queue, and forward payloads
to self-chosen URLs only after DNS-resolving and blocking private/link-local
targets.

## Procedure

1. **Handshake.** On a GET with `hub.mode=subscribe`, check `hub.verify_token`
   against the configured token; if it matches, echo `hub.challenge` (200).
   Otherwise 403. Meta-specific; other providers skip it.
2. **Verify the signature.** Look up the provider in the config table and
   compute the expected HMAC over the raw body. Compare in constant time.
   If missing or wrong → 401, log the attempt, do not process.
3. **Check the replay window.** Stripe rejects if
   `now - event.created > 5 min`. GitHub/Meta have no documented window, so
   apply a configurable window with a hard cap and treat an out-of-window
   delivery as a **replay** (idempotent re-process), not a rejection.
4. **Dedupe.** Look up the event id in the idempotency table. If present and
   completed → 200 ack. If present and pending → 202 (do not re-run). If
   absent → insert pending, process, mark completed.
5. **Process.** Apply the change to the Ottili ledger. On exception → leave
   pending, increment the failure count, move to dead-letter after N attempts.
6. **Ack.** 200 only after the ledger write is durable.

## Decision tables

### Signature schemes per provider

| Provider | Header | Algorithm | Replay window |
|---|---|---|---|
| Meta | `hub.verify_token` GET challenge | none (token match) | n/a |
| GitHub | `X-Hub-Signature-256` | HMAC-SHA256, `sha256=` prefix | configurable |
| Stripe | `Stripe-Signature` | HMAC-SHA256 over `t,{v1}`, `t` = epoch seconds | **5 min** |
| Twilio | `X-Twilio-Signature` | HMAC-SHA256 over URL + params + body | configurable |
| DHL | webhook secret | HMAC-SHA256 over raw body | configurable |

## Pitfalls from research

- There is **no universal webhook signature**. Computing the wrong algorithm
  per provider is the most common failure.
- **A replay is not a rejection.** A completed replay is acked without side
  effects; only a pending replay is held.
- **Out-of-order delivery is real.** Versioning state per aggregate and
  buffering is safer than dropping.
- **SSRF defence is mandatory** for any URL an agent is asked to deliver to
  (OWASP checklist). Resolve DNS at request time and block private/link-local.

## Verification checklist

- [ ] Provider identified; correct signature algorithm used
- [ ] Signature verified in constant time; bad sig → 401, not processed
- [ ] Replay window checked per provider
- [ ] Event id deduped; completed replay acked without side effects
- [ ] Out-of-order events buffered per aggregate
- [ ] Failures moved to dead-letter with raw payload preserved
- [ ] Forwarded URL DNS-resolved at request time; private/link-local blocked

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
- [Design](references/DESIGN.md)
