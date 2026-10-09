# SOURCES — webhooks-safe

Retrieval date: 2026-10-09 (all URLs fetched with `curl` on that date unless
noted). Version-sensitive facts are pinned in `config/versions.json` and
never hardcoded in logic. Re-verify each provider's signature scheme before
every build and record the retrieval date here. Conflicts between sources are
noted at the end.

## Primary sources (re-verified 2026-10-09)

| # | Source | URL | HTTP | Notes |
|---|---|---|---|---|
| 1 | GitHub — webhooks docs | https://docs.github.com/webhooks | 200 | Authoritative signature scheme: `X-Hub-Signature-256`, HMAC-SHA256 over the raw body. Retrieved 2026-10-09. |
| 2 | GitHub — webhook events and payloads | https://docs.github.com/webhooks/webhook-events-and-payloads | 200 | Delivery id and event id contract. Retrieved 2026-10-09. |
| 3 | Stripe — webhooks docs | https://stripe.com/docs/webhooks | 200 | `Stripe-Signature` header with `t=<ts>,v1=<hex>`; 5-minute replay window. Retrieved 2026-10-09. |
| 4 | Twilio — webhooks docs | https://www.twilio.com/docs/usage/webhooks | 200 | Webhook delivery contract. Retrieved 2026-10-09. |
| 5 | Twilio — security (signature header) | https://www.twilio.com/docs/usage/security | 200 | Confirms the `X-Twilio-Signature` header exists. The exact HMAC input (URL + body + params) is **unverified** at this retrieval — the docs page did not expose the algorithm text to a plain-text crawl. Treat Twilio as unverified. Retrieved 2026-10-09. |
| 6 | PayPal — API webhooks v1 | https://developer.paypal.com/docs/api/webhooks/v1 | 200 | Webhook API entry point. Retrieved 2026-10-09. |
| 7 | PayPal — webhook event types | https://developer.paypal.com/docs/api/webhooks/v1/webhooks | 404 | The event-types page 404s; the v1 root (row 6) is live. The `X-PayPal-Signature` header name is documented from memory and marked **unverified**. Retrieved 2026-10-09. |
| 8 | OWASP — SSRF prevention cheat sheet | https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html | 200 | Allow-list based outbound URL validation. Retrieved 2026-10-09. |
| 9 | OWASP — web security testing guide (SSRF) | https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/07-04-Test_for_Server_Side_Request_Forgery | 200 | SSRF test procedures. Retrieved 2026-10-09. |

## URLs that moved or 404'd (re-verified 2026-10-09)

| Old URL | Status | Replacement |
|---|---|---|
| `developer.paypal.com/docs/checkout/webhooks` | 404 | `developer.paypal.com/docs/api/webhooks/v1` (200) |
| `developer.paypal.com/docs/checkout/webhooks/webhooks-overview` | 404 | unverified — see row 7 |
| `developer.paypal.com/docs/api/webhooks/v1/webhooks` | 404 | unverified — see row 7 |
| OWASP `www-community/attacks/Webhook_Security` | 404 | cheat sheet + testing guide (rows 8-9) |

## Version-sensitive notes

- **HMAC-SHA256 is stable** (NIST SP 800-38B); no version pin needed. Secret
  key length must be >= 256 bits; rotate on compromise.
- **Provider signature schemes change.** GitHub and Stripe are verified;
  PayPal and Twilio are **unverified** at this retrieval. The scripts fall
  back to plain HMAC-SHA256 and the skill flags the result.
- **PayPal's docs restructured.** The old `docs/checkout/webhooks` paths all
  404; the live entry point is `docs/api/webhooks/v1`. The signature header
  name is unverified until a PayPal business account confirms it.
- **Idempotency TTL** is configurable per provider; default 24h. Pin in config.

## Conflicts / open questions

- **PayPal signature scheme is unverified.** The `X-PayPal-Signature` header
  name and algorithm are documented from memory; the live docs page does not
  expose them to a plain-text crawl. Flag in the skill and re-fetch at build
  time with a browser user agent.
- **Twilio signature input is unverified.** `X-Twilio-Signature` exists (row 5)
  but the exact HMAC input (URL + body + params) is not confirmed. Treat as
  unverified; the script uses plain HMAC over the raw body as a fallback.
- No provider publishes a stable "version" for webhook schemes; the retrieval
  date is the pin.
