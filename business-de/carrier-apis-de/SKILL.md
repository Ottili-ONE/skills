---
name: carrier-apis-de
description: "Ship parcels with German carriers (DHL, DPD, GLS, Hermes, UPS) via official REST/SOAP APIs only — never by scraping tracking pages. Use when an agent must create or cancel a label, track a shipment, print a return label, or reconcile carrier charges. Not for private senders, freight, or non-DE carriers."
license: MIT-compat
compatibility: "framework-agnostic; DHL Parcel DE REST v2.2.0, Tracking v1.0.0, Returns v1.1.0; offline validation"
metadata: {}
allowed-tools: []
---

# carrier-apis-de

## When to use this skill

Use this skill when an Ottili agent must create, cancel, track or reconcile a
shipment with a German carrier (DHL, DPD, GLS, Hermes, UPS) through the
**official API**. It applies to label creation, returns, tracking and charge
reconciliation. Do **not** use it for private (Selbstzahler) senders, freight,
or for tracking via the public carrier website.

## Description

Create, cancel, track and reconcile German-carrier shipments via official APIs
only. DHL Parcel DE (REST v2) is the only carrier with a fully readable primary
specification this pass; DPD, GLS, Hermes and UPS facts are marked
**unverified** and must be re-fetched from the partner portals before an audit.

## Procedure

1. **Choose the provider.** DHL Parcel DE REST v2 is primary. DPD/GLS/Hermes/UPS
   share the same integration pattern (idempotency key, label POST, tracking
   webhook) but their specs are unverified — document the pattern, flag the
   gaps, and re-verify before relying on a carrier-specific fact.
2. **Authenticate.** OAuth2 ROPC against the DHL Authentication API; cache the
   token and refresh on 401. Sandbox creds are `user-valid` /
   `SandboxPasswort2023!`. Basic Auth is deprecated.
3. **Create a shipment (idempotent).** `POST /orders` with a client-generated
   `clientReferenceNo`. On 409/5xx, retry with the **same** key — never a new
   one. A duplicate key returns the existing shipment.
4. **Read the label.** The response carries the label as a binary blob
   (PDF/PNG) plus the shipment number and routing code. Persist both.
5. **Manifest.** Shipments are not handed over until `POST /manifest` (or the
   automatic end-of-day close at 17:45). A manifested shipment **cannot be
   edited** — only deleted and re-created before manifest.
6. **Track.** Use the Shipment Tracking API in `business` mode for EKP-scoped
   data. Never scrape www.dhl.de.
7. **Reconcile.** Match carrier charges to the Ottili ledger by
   `clientReferenceNo`. A charge with no ledger entry is an `unknown_result`,
   not an error.

## Decision tables

### Provider readiness

| Carrier | API surface | Verified | Action |
|---|---|---|---|
| DHL Parcel DE | REST v2.2.0 / Tracking v1.0.0 / Returns v1.1.0 | yes | use directly |
| DPD DE | REST (myDPD portal) | **no** | document pattern, re-verify |
| GLS Group | SOAP/REST + ParcelWatch | **no** | document pattern, re-verify |
| Hermes / OnTrac | partner portal | **no** (403 at fetch) | document pattern, re-verify |
| UPS | Shipping/Tracking/Rating APIs | **no** (shell only) | document pattern, re-verify |

## Pitfalls from research

- **Never scrape tracking pages.** DPD moved tracking behind a postal-code
  privacy gate, GLS behind Cloudflare, UPS bot-protects its endpoint (Apify,
  verified 2026-09-02). Use official APIs and webhooks only.
- **Manifest lock is the #1 production incident.** A PATCH on a manifested
  shipment silently fails or is rejected; recreate before manifest.
- **Idempotency key must be stable.** Regenerating the key on retry creates a
  duplicate label and duplicate charges.
- **DPD/GLS/Hermes/UPS specs are unverified this pass.** Any carrier-specific
  fact below this line is a claim, not a verified fact.

## Verification checklist

- [ ] Provider selected from the readiness table
- [ ] OAuth2 token obtained and cached; 401 handled
- [ ] `clientReferenceNo` reused on every retry
- [ ] Label bytes + shipment number persisted
- [ ] Manifest state checked before any edit
- [ ] Tracking via official API only
- [ ] Charges reconciled by reference; unknown results flagged

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
- [Design](references/DESIGN.md)
