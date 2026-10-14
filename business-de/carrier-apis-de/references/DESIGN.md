# DESIGN — carrier-apis-de

## Trigger description (draft for SKILL.md front matter)

> Use this skill when an Ottili agent needs to create, cancel, track or
> reconcile shipments with a German carrier (DHL, DPD, GLS, Hermes, UPS) via
> the **official REST/SOAP APIs only** — never by scraping tracking pages.
> Triggers: "create a DHL label", "track this shipment", "print a return
> label", "reconcile carrier charges", "which carrier API do I use".

## What this skill does better than a generic agent

- **Pins the exact API surface per carrier** (DHL Shipping v2.0.2, Tracking
  v1.0.0, Returns v1.1.0) instead of guessing from a search result.
- **Idempotency is a first-class concept**: every label POST carries a
  client-generated idempotency key; the skill defines the retry-with-same-key
  rule and the "unknown result" reconciliation procedure.
- **Explicitly bans scraping** (DPD privacy gate, GLS Cloudflare, UPS
  bot-protection) and mandates official APIs + webhooks.
- **Copy-paste-safe curl examples** with sandbox credentials, so an agent can
  prove the flow works before wiring it into production.

## Procedure outline

1. **Choose the provider interface.** DHL Parcel DE (REST v2) is the only one
   with a fully readable primary spec this pass. DPD/GLS/Hermes/UPS require a
   business contract; the skill documents the common pattern and marks each
   fact unverified.
2. **Authenticate.** OAuth2 ROPC against the DHL Authentication API. Cache the
   token; refresh on 401. Sandbox creds: `user-valid` / `SandboxPasswort2023!`.
3. **Create a shipment (idempotent).** `POST /orders` with a `clientReferenceNo`
   (the idempotency key). On a 409/5xx, retry with the **same** key; never
   generate a new one.
4. **Read the label.** The response contains the label as a binary blob
   (PDF/PNG) plus shipment number and routing code. Persist both.
5. **Manifest.** Shipments are not handed over until `POST /manifest` (or the
   automatic end-of-day closing at 17:45). A manifested shipment **cannot be
   edited** — only deleted and re-created before manifest.
6. **Track.** Use the Shipment Tracking API (`business` mode for EKP-scoped
   data). Never scrape www.dhl.de.
7. **Reconcile.** Match the carrier's returned charges to the Ottili ledger by
   `clientReferenceNo`; a charge with no ledger entry is an unknown result,
   not an error.

## Scripts planned

| Script | Purpose |
|---|---|
| `scripts/create_label.py` | Idempotent label creation: takes provider config + order JSON, returns label bytes + shipment number, retries with the same idempotency key. |
| `scripts/track_shipment.py` | Official tracking query; exits non-zero on an unknown tracking number. |
| `scripts/reconcile_charges.py` | Matches carrier charge lines to ledger entries by reference; reports unknown results. |

## Five eval prompts

1. **Idempotency.** "Create two DHL labels with the same `clientReferenceNo`.
   What should happen?" → The second call returns the **same** label/shipment
   number, not a duplicate. Failure sign: two different shipment numbers for
   one order.
2. **Manifest lock.** "A shipment was manifested. Can I edit its address?"
   → No. `DELETE /orders` is also blocked post-manifest; recreate before
   manifest. Failure sign: silently PATCHing a manifested shipment.
3. **Unknown tracking number.** "Track `12345678901234567890`." → Exit
   non-zero with a structured "unknown" error, not a scraped HTML page.
4. **Scraping ban.** "The DPD tracking page shows 'privacy gate' for my
   postal code. Can I scrape around it?" → No — use the official DPD API or
   webhook. Failure sign: attempting a GET on the public tracking URL.
5. **Reconciliation gap.** "The carrier charged EUR 4.95 but the ledger has
   no matching order." → Flag as `unknown_result`, do not write off. Failure
   sign: auto-allocating to "shipping expense".
