# Procedures — carrier-apis-de

Versions are pinned in `config/versions.json`; never hardcode a version in
scripts. DHL facts are verified; DPD/GLS/Hermes/UPS facts are **unverified**
until re-fetched from the partner portals.

## 1. Choose the provider

| Carrier | API | Verified | Action |
|---|---|---|---|
| DHL Parcel DE | REST v2.2.0 / Tracking v1.0.0 / Returns v1.1.0 | yes | use directly |
| DPD DE | REST (myDPD portal) | **no** | document pattern, re-verify |
| GLS Group | SOAP/REST + ParcelWatch | **no** | document pattern, re-verify |
| Hermes / OnTrac | partner portal | **no** (403 at fetch) | document pattern, re-verify |
| UPS | Shipping/Tracking/Rating | **no** (shell only) | document pattern, re-verify |

## 2. Authenticate (DHL)

OAuth2 ROPC against the DHL Authentication API. Cache the token; refresh on
401. Sandbox creds: `user-valid` / `SandboxPasswort2023!`. Basic Auth is
deprecated.

## 3. Create a shipment (idempotent)

`POST /orders` with a client-generated `clientReferenceNo`. On 409/5xx,
retry with the **same** key — never a new one. A duplicate key returns the
existing shipment.

## 4. Read the label

The response carries the label as a binary blob (PDF/PNG) plus the shipment
number and routing code. Persist both.

## 5. Manifest

Shipments are not handed over until `POST /manifest` (or the automatic
end-of-day close at 17:45). A manifested shipment **cannot be edited** —
only deleted and re-created before manifest.

## 6. Track

Use the Shipment Tracking API in `business` mode for EKP-scoped data. Never
scrape www.dhl.de. Public tracking endpoints are unreliable for automation.

## 7. Reconcile

Match carrier charges to the Ottili ledger by `clientReferenceNo`. A charge
with no ledger entry is an `unknown_result`, not an error.

## Worked examples

### Good — idempotent label creation

```
POST /orders {clientReferenceNo: "ord-2026-0001", ...}
-> 201 {shipmentNumber: "1234567890123456", label: <PDF>}
Retry with the same clientReferenceNo -> 200 {shipmentNumber: "1234567890123456", ...}
=> same shipment, no duplicate
```

### Bad — new idempotency key on retry

```
POST /orders {clientReferenceNo: "ord-2026-0001"} -> 201
POST /orders {clientReferenceNo: "ord-2026-0001-v2"} -> 201 (new shipment)
=> duplicate label and duplicate charge
```
