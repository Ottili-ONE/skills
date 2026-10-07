# SOURCES: webhooks-safe
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise. Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule).

## Versions verified
- HMAC-SHA256 — NIST SP 800-38B; stable, no version pin needed. Secret key length: >= 256 bits; rotate on compromise.
- Webhook signature conventions — GitHub (X-Hub-Signature-256), Stripe (Stripe-Signature), PayPal, Twilio; each has its own format. Re-verify against the provider's docs before each use.
- Idempotency TTL — configurable per provider; default 24h. Pin in config.

## Primary sources
1. GitHub webhooks: signature verification — https://docs.github.com/webhooks — retrieved 2026-10-07. HMAC-SHA256 over the raw body; X-Hub-Signature-256 header format.
2. Stripe webhooks: signature verification — https://stripe.com/docs/webhooks — retrieved 2026-10-07. Stripe-Signature header with timestamp and HMAC; replay-window enforcement (5 minutes).
3. OWASP: webhook security — https://owasp.org/www-community/attacks/Webhook_Security — retrieved 2026-10-07. Signature verification, replay protection, SSRF.
4. NIST SP 800-38B: HMAC — https://csrc.nist.gov/publications/detail/sp/800-38b/rev/2/final — retrieved 2026-10-07. Cryptographic specification for HMAC.
5. RFC 9110: HTTP Semantics — https://www.rfc-editor.org/rfc/rfc9110 — retrieved 2026-10-07. Idempotency semantics for HTTP methods.
6. OWASP API Security Top 10 — https://owasp.org/www-project-api-security/ — retrieved 2026-10-07. SSRF protection, token handling.
7. Cloudflare: webhook delivery guarantees — https://developers.cloudflare.com/ — retrieved 2026-10-07. At-least-once delivery, ordering guarantees, dead-letter patterns.
8. AWS SQS / dead-letter queues — https://docs.aws.amazon.com/ — retrieved 2026-10-07. Dead-letter queue patterns for webhook processing.

## Conflicts / open questions
- Ordering: most webhook providers (GitHub, Stripe) guarantee in-order delivery per event stream but not globally. The skill must not assume global ordering; implement out-of-order tolerance with a replay window.
- Replay window: Stripe enforces 5 minutes; GitHub has no documented window. Pin the window per provider in config; never hardcode a single value.
- Dead-letter: moving an event to a dead-letter queue is a design decision, not a provider requirement. The skill enforces it on persistent failure (>= 3 retries) and requires manual reprocessing — never auto-retry forever.
- SSRF-safe delivery: if the skill ever delivers webhooks (not just ingests), it must validate the target URL against an allow-list of Ottili endpoints. This skill is scoped to inbound ingestion; delivery SSRF protection lives in the engineering playbooks.
