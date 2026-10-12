# SOURCES — webhooks-safe

Retrieval date: 2026-10-12. Every URL below was probed on that date;
the HTTP status is recorded per row. Version-sensitive facts are pinned in
`config/versions.json`; re-verify before relying on a fact.

| # | Source | URL | Retrieved | Verified version | Notes |
|---|---|---|---|---|---|
| 1 | Meta for Developers — Webhooks Getting Started | https://developers.facebook.com/docs/graph-api/webhooks/getting-started | 2026-10-12 | **200 OK** | Primary. Confirms the hub.mode/hub.challenge/hub.verify_token verification handshake, HTTPS-only endpoints, no self-signed certs, and the two-request model (GET verification + POST event). |
| 2 | Meta — Webhooks Edge Reference | https://developers.facebook.com/docs/graph-api/webhooks | 2026-10-12 | **200 OK** | Confirms object/field subscription model and the `entry[]`/`changes[]` payload shape. |
| 3 | GitHub — Webhooks | https://docs.github.com/en/webhooks | 2026-10-12 | **200 OK** | Confirms the `X-Hub-Signature-256` = `sha256=HMAC(payload, secret)` webhook signature and the `X-GitHub-Delivery` idempotency header. |
| 4 | Stripe — Webhooks | https://docs.stripe.com/webhooks | 2026-10-12 | **200 OK** | Confirms `Stripe-Signature` = `t, v1` HMAC over `timestamp.body`, the replay-window rule (reject if `now - timestamp > 5 min`), and the event-id dedup table. |
| 5 | Twilio — Webhooks | https://www.twilio.com/docs/usage/webhooks | 2026-10-12 | **200 OK** | Confirms the `X-Twilio-Signature` = HMAC over `URL + sorted params + body` and the auth-token-based verification. |
| 6 | OWASP — SSRF (Web Security Testing Guide) | https://owasp.org/www-project-web-security-testing-guide/latest/04-Web_Application_Security_Testing/07-Input_Validation_Testing/08-Server_Side_Request_Forgery | 2026-10-12 | **200 OK** | Primary for the SSRF-defence checklist: resolve DNS at request time, block RFC 1918/loopback/link-local, validate redirect behaviour, cap redirects. |
| 7 | WordPress.org — REST API Handbook | https://developer.wordpress.org/rest-api/ | 2026-10-12 | **200 OK** | Confirms WP REST API authentication (Application Passwords, OAuth 2) and that WP has **no native inbound webhook endpoint** — outbound webhooks come from plugins, so an Ottili agent must not assume a built-in WP webhook surface. |
| 8 | WordPress.org — REST API reference (posts) | https://developer.wordpress.org/rest-api/reference/posts/ | 2026-10-12 | **200 OK** | Confirms the `/wp-json/wp/v2/posts` endpoint shape and the `Authorization: Basic` / OAuth2 auth modes used by `publish-reconcile-wp-meta`. |
| 9 | R3_VERIFIED_FACTS.md | ../ottili-planning/inputs/R3_VERIFIED_FACTS.md | 2026-10-06 | — | starting point; re-verified 2026-10-12. |

## Conflicts / version-sensitive notes

- **Signature schemes differ per provider** — there is no universal webhook signature. The skill computes the right algorithm per provider from a config table rather than assuming one.
- **WordPress has no inbound webhooks.** The WP REST API handbook confirms outbound publishing only. Any "WP webhook" expectation must be routed through a plugin; the skill's outbound side uses the REST API directly.
- **Meta requires HTTPS with a valid TLS cert** (no self-signed). The verification GET must echo `hub.challenge` only after the `hub.verify_token` check.
- **Replay window is provider-specific**: Stripe mandates 5 minutes; GitHub/Meta have no documented time window, so the skill applies a configurable window with a hard cap and treats an out-of-window delivery as a **replay** (idempotent re-process), not a rejection.
- **SSRF defence is mandatory for any URL an agent is asked to deliver to.** The OWASP checklist is the reference; the skill's `webhook_forward.py` resolves DNS at request time and blocks private/link-local targets.
