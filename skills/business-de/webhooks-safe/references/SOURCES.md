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
| 3 | Stripe — webhooks docs | https://docs.stripe.com/webhooks | 200 | `Stripe-Signature` header with `t=<ts>,v1=<hex>`; 5-minute replay window. Retrieved 2026-10-09. `stripe.com/docs/webhooks` 301-redirects to this URL. |
| 4 | Twilio — webhooks docs | https://www.twilio.com/docs/usage/webhooks | 200 | Webhook delivery contract. Retrieved 2026-10-09. |
| 5 | Twilio — security (signature header) | https://www.twilio.com/docs/usage/security | 200 | Confirms the `X-Twilio-Signature` header exists. The exact HMAC input (URL + body + params) is **unverified** at this retrieval — the docs page did not expose the algorithm text to a plain-text crawl. Treat Twilio as unverified. Retrieved 2026-10-09. |
| 6 | PayPal — API webhooks v1 | https://developer.paypal.com/docs/api/webhooks/v1 | 200 | Webhook API entry point. Retrieved 2026-10-09. |
| 7 | PayPal — webhook overview | https://developer.paypal.com/docs/api/webhooks/overview | 200 | Live overview page; confirms the webhook API family exists. The `X-PayPal-Signature` header name and algorithm are **unverified** at this retrieval — the overview page does not expose the signature scheme to a plain-text crawl. Retrieved 2026-10-09. |
| 8 | OWASP — SSRF prevention cheat sheet | https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html | 200 | Allow-list based outbound URL validation. Retrieved 2026-10-09. |
| 9 | OWASP — web security testing guide (SSRF) | https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/07-04-Test_for_Server_Side_Request_Forgery | 200 | SSRF test procedures. Retrieved 2026-10-09. |

## URLs that moved or 404'd (re-verified 2026-10-09)

| Old URL | Status | Replacement |
|---|---|---|
| `developer.paypal.com/docs/checkout/webhooks` | 404 | `developer.paypal.com/docs/api/webhooks/v1` (200) |
| `developer.paypal.com/docs/checkout/webhooks/webhooks-overview` | 404 | unverified — see row 7 |
| `developer.paypal.com/docs/api/webhooks/v1/webhooks` | 404 | `developer.paypal.com/docs/api/webhooks/overview` (200) |
| OWASP `www-community/attacks/Webhook_Security` | 404 | cheat sheet + testing guide (rows 8-9) |

## Version-sensitive notes

- **HMAC-SHA256 is stable** (NIST SP 800-38B); no version pin needed. Secret
  key length must be >= 256 bits; rotate on compromise.
- **Provider signature schemes change.** GitHub and Stripe are verified;
  PayPal and Twilio are **unverified** at this retrieval. The scripts fall
  back to plain HMAC-SHA256 and the skill flags the result.
- **PayPal's docs restructured.** The old `docs/checkout/webhooks` paths all
  404; the live entry point is `docs/api/webhooks/v1` and the overview is at
  `docs/api/webhooks/overview`. The signature header name and algorithm are
  unverified until a PayPal business account confirms them.
- **Idempotency TTL** is configurable per provider; default 24h. Pin in config.

## Conflicts / open questions

- **PayPal signature scheme is unverified.** The `X-PayPal-Signature` header
  name and algorithm are documented from memory; the live overview page does
  not expose them to a plain-text crawl. Flag in the skill and re-fetch at
  build time with a browser user agent.
- **Twilio signature input is unverified.** `X-Twilio-Signature` exists (row 5)
  but the exact HMAC input (URL + body + params) is not confirmed. Treat as
  unverified; the script uses plain HMAC over the raw body as a fallback.
- No provider publishes a stable "version" for webhook schemes; the retrieval
  date is the pin.

## Re-check 2026-10-13 (PASS 3 of skills-business-de-r3-01)

Two random sources per skill re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-13. Nothing was copied verbatim from any source; all SKILL.md prose is original.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://docs.github.com/webhooks | 200 | GitHub webhooks docs resolve; signature is HMAC-SHA256 over the raw body |
| https://docs.stripe.com/webhooks | 200 | Stripe webhooks docs resolve; signature in the SvCb header, replay-window guidance confirmed |

## Re-check 2026-10-14 (PASS 3 of skills-business-de-r3-01)

Re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-14.
Two statute portals re-confirmed still 404; the dejure.org mirrors carry the
authoritative text. Nothing was copied verbatim from any source.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://www.cen.eu/standards/EN/16931 | 200 | CEN EN 16931 standard page resolves |
| http://fnfe-mpe.org/factur-x/ | 200 | Factur-X / ZUGFeRD page resolves; Factur-X 1.09.2 / ZUGFeRD 2.5.2 confirmed |
| https://www.ferd-net.de/standards/zugferd | 200 | FeRD ZUGFeRD page resolves; 2.5.2 confirmed |
| https://github.com/itplr-kosit/validator-configuration-xrechnung | 200 | KoSIT config repo resolves; tag v2026-08-31 is the pinned version |
| https://dejure.org/gesetze/UStG/14 | 200 | UStG §14 e-invoicing obligation text resolves |
| https://dejure.org/gesetze/UStG/13b | 200 | UStG §13b "Leistungsempfänger als Steuerschuldner" (reverse charge) resolves — confirms the PASS-2 renumber from §3g |
| https://www.gesetze-im-internet.de/ustg/ | 404 | UStG page still 404 (re-confirmed); use dejure.org mirror |
| https://www.gesetze-im-internet.de/ao/ | 404 | AO page still 404 (re-confirmed); use dejure.org or steuer-berater.de mirror |
| https://www.datev.de/ | 200 | datev.de home resolves; EXTF spec is gated behind partner registration |
| https://github.com/seamless-engineering/datev-extf | 200 | EXTF repo resolves; raw columns.ts is the authoritative column table |
| https://www.whk-controlling.de/ | 200 | GoBD retention classes resolve; 6/8/10 split confirmed |

**Net effect on pinned versions: none.** Every version in
`config/versions.json` is still current as of 2026-10-14. The two statute
portals remain the weak links — mark them "re-fetch before audit" rather than
trusting the corroboration.

## Re-verification 2026-10-15 (PASS 5 of skills-business-de-r3-05)

Re-fetched every primary source with `curl -s -o /dev/null -w "%{http_code}"
--max-time 20 -L` on 2026-10-15. Full table: `config/REVERIFY_2026-10-15.md`.

- **dejure.org mirror fixed:** `https://dejure.org/gesetze/AO` now returns
  **200**; the `.html` variant still 404s. SOURCES entries that pointed at the
  old suffix are corrected here.
- **No version pin moved.** CEN EN 16931, FNFE-MPE Factur-X 1.09.2, KoSIT
  `v2026-08-31`, PayPal webhooks and the DHL API catalog all still 200 with
  the same effective versions.
- **Still flaky (000/404 at both 2026-10-14 and 2026-10-15):**
  `gesetze-im-internet.de/beg/`, `/ao/`, `/ustg/`, `akretion.github.io/factur-x/`,
  `bundesbank.de/...iban`, and the DPD developer portal (200 body is a
  redirect to `seite-nicht-gefunden`). Corroborate with the recorded mirrors
  before an audit.
