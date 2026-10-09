---
name: carrier-apis-de
description: "Integrate German carrier APIs (DHL, DPD, GLS, Hermes, UPS) for Ottili flows: create idempotent labels, track via official APIs only and reconcile label costs. Use when an agent must create a shipping label, track a shipment, or reconcile carrier API responses. Not for general shipping logic or unofficial tracking scrapers."
license: MIT-compat
compatibility: "framework-agnostic; German carrier REST/XML/SOAP APIs; offline validation"
metadata: {}
allowed-tools: []
---

# carrier-apis-de

## When to use this skill

Use this skill when an agent must talk to a German carrier API
(DHL, DPD, GLS, Hermes, UPS) for Ottili flows: create a shipping
label, track a shipment, or reconcile label cost and status against
the Ottili shipping record. Do **not** use it for general shipping
logic (packing, routing, address validation) or for unofficial
tracking scrapers — every carrier here has an official API and a
contract; use it.

## Procedure

1. **Identify the carrier and its contract model.** Each carrier has a
   different auth and API shape; never assume one fits another.
2. **Authenticate with the carrier's documented flow** (OAuth2 client
   credentials or token exchange); cache the token and refresh before
   expiry; never hardcode credentials.
3. **Create an idempotent label.** Every label request carries a
   client-generated `Idempotency-Key`. On a duplicate key the carrier
   returns the existing label — never create a second.
4. **Track via the official API only.** Poll the carrier's tracking
   endpoint; cache results; never scrape the public tracking page.
5. **Reconcile.** Compare label cost and status against the Ottili
   shipping record; on an unknown result re-query by tracking number
   and log the reconciliation.
6. **Handle errors via the fix table.** Map carrier error codes to a
   concrete fix; never retry auth errors.

## Decision tables

### Carrier contract model

| Carrier | API | Auth | Idempotency header | Sandbox |
|---|---|---|---|---|
| DHL Parcel DE | REST v3 | OAuth2 (consumer key/secret + token) | `X-Request-ID` | yes |
| DPD Germany | XML/JSON | API key + DPD-Auth token | shipment reference (body) | yes |
| GLS Germany | SOAP/REST | API key + secret | `labelId` (client-generated) | no public sandbox |
| Hermes Germany | REST | OAuth2 / API key | `correlationId` | business account required |
| UPS Germany | REST | OAuth2 client credentials | `X-Inbound-Idempotency-Key` | yes (CIM) |

### Label error → fix

| Carrier status | Meaning | Fix |
|---|---|---|
| 401 / 403 | Auth failure | Re-issue token; never retry with the same token |
| 409 | Conflict / duplicate key | Re-query by reference; never re-create |
| 422 | Validation error | Fix the field named in the response body |
| 429 | Rate limited | Exponential backoff, up to 3 attempts |
| 5xx | Carrier outage | Retry with backoff; mark the label unknown |

## Pitfalls from research

- **Idempotency key names differ per carrier.** DHL uses `X-Request-ID`,
  UPS uses `X-Inbound-Idempotency-Key`, DPD/GLS use a reference field in
  the body. Abstract the key behind a per-carrier adapter; never assume
  one header name.
- **A duplicate key does not always mean "return existing".** Some
  carriers return 409 and you must re-query by the reference number to
  find the existing label. Treat 409 as "re-query, never re-create".
- **Never scrape the tracking page.** Every carrier has an official
  tracking API; scraping breaks on layout changes and violates the
  carrier's terms. Use the API and cache results.
- **Sandbox availability varies.** DHL, DPD and UPS offer sandboxes;
  GLS and Hermes do not (Hermes requires a business account). Treat
  sandbox tests as optional and document which carriers support them.
- **Label cost reconciliation is not optional.** A label that was
  created but never reconciled silently diverges from the Ottili
  shipping record. Reconcile on every label, not after the fact.

## Verification checklist

- [ ] Carrier and contract model identified
- [ ] Auth token cached and refreshed before expiry
- [ ] Idempotency key present and client-generated
- [ ] Duplicate key returns the existing label (or 409 → re-query)
- [ ] Tracking uses the official endpoint, never a web page
- [ ] Results cached; no hammering
- [ ] Label cost/status reconciled with Ottili shipping record
- [ ] Error codes mapped to the fix table; auth errors never retried

## References

- [Procedures, worked examples and carrier API summaries](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
- [Scripts](scripts/)
