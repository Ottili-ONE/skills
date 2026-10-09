# SOURCES — webhooks-safe

Retrieval date: 2026-10-09 (all URLs fetched with `curl` on that date unless
noted). Version-sensitive facts are pinned in `config/versions.json` and
never hardcoded in logic. Re-verify each provider's signature scheme before
every build and record the retrieval date here. Conflicts between sources are
noted at the end.

## Primary sources (verified 2026-10-09)

| # | Source | URL | HTTP | Notes |
|---|---|---|---|---|
| 1 | GitHub — webhooks docs | https://docs.github.com/webhooks | 200 | Authoritative signature scheme: `X-Hub-Signature-256`, HMAC-SHA256 over the raw body. Retrieved 2026-10-09. |
| 2 | GitHub — webhook events and payloads | https://docs.github.com/webhooks/webhook-events-and-payloads | 200 | Delivery id and event id contract. Retrieved 2026-10-09. |
| 3 | Stripe — webhooks docs | https://stripe.com/docs/webhooks | 200 | `Stripe-Signature` header with `t=<ts>,v1=<hex>`; 5-minute replay window. Retrieved 2026-10-09. |
| 4 | OWASP — SSRF prevention cheat sheet | https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html | 200 | Allow-list based outbound URL validation. Retrieved 2026-10-09. |
| 5 | OWASP — web security testing guide (SSRF) | https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/07-04-Test_for_Server_Side_Request_Forgery | 200 | SSRF test procedures. Retrieved 2026-10-09. |

## Version-sensitive notes

- **HMAC-SHA256 is stable** (NIST SP 800-38B); no version pin needed. Secret
  key length must be >= 256 bits; rotate on compromise.
- **Provider signature schemes change.** GitHub, Stripe, PayPal and Twilio
  each have their own header format and replay window. Re-verify against the
  provider's docs before each use; pin the confirmed values in config.
- **Idempotency TTL** is configurable per provider; default 24h. Pin in config.

## Conflicts / open questions

- The older OWASP `www-community/attacks/Webhook_Security` URL returns 404
  (2026-10-09); the cheat sheet and the testing guide are the authoritative
  OWASP references and are used instead.
- PayPal and Twilio signature schemes are listed from memory and marked
  **unverified** until their docs are fetched at build time.
- No provider publishes a stable "version" for webhook schemes; the retrieval
  date is the pin.
