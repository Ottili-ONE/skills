# Procedures — carrier-apis-de

All carrier API versions are read from `config/versions.json` (never hardcode).
Carriers update APIs without a public changelog; re-verify against each
developer portal before every build and record the retrieval date in
`references/SOURCES.md`.

## 1. Identify the carrier and its contract model

| Carrier | API shape | Auth | Idempotency field | Sandbox |
|---|---|---|---|---|
| DHL Parcel DE | REST v3 | OAuth2: consumer key/secret → access token | `X-Request-ID` (header) | yes |
| DPD Germany | XML/JSON | API key + DPD-Auth token | shipment reference (body) | yes |
| GLS Germany | SOAP/REST | API key + secret | `labelId` (client-generated) | none public |
| Hermes Germany | REST | OAuth2 / API key | `correlationId` | business account |
| UPS Germany | REST | OAuth2 client credentials | `X-Inbound-Idempotency-Key` | yes (CIM) |

DHL auth flow (verified 2026-10-09 against developer.dhl.com):
`POST https://developer-api.dhl.com/soap/v2/token` with `grant_type=client_credentials`
(no refresh-token step in v3; re-issue on every expiry). Cache the token
in memory; never log it. DPD uses a separate `DPD-Auth` token obtained from
the DPD login endpoint; the API key is sent on every call.

**Thresholds:** token refresh at least 60 s before expiry; retry budget of
3 attempts per request; backoff base 500 ms, factor 2, cap 30 s.

## 2. Create an idempotent label

Every label request MUST carry a client-generated idempotency key. The key
is your own order/shipment reference; it must be stable across retries.

```bash
# DHL: header X-Request-ID
curl -s -X POST "$DHL_LABEL_URL" \
  -H "X-Request-ID: $MY_REF" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d @label.json

# UPS: header X-Inbound-Idempotency-Key
curl -s -X POST "$UPS_LABEL_URL" \
  -H "X-Inbound-Idempotency-Key: $MY_REF" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d @label.json

# DPD/GLS/Hermes: key in the body
curl -s -X POST "$DPD_LABEL_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d @label.json   # body carries shipmentReferenceNumber / labelId / correlationId
```

**Good output** (DHL, first call):
```json
{"shipmentNumber":"12345678901234567890","labelUrl":"https://...","cost":{"amount":12.50,"currency":"EUR"}}
```
**Bad output** — two labels created for one order because the agent retried
without the key:
```json
[{"shipmentNumber":"...A","cost":12.50},{"shipmentNumber":"...B","cost":12.50}]
```
Detect it: two distinct `shipmentNumber` values for the same `MY_REF`. The
reconcile script flags it as a cost delta against the Ottili shipping record.

## 3. Duplicate-key handling

| Carrier response | Meaning | Action |
|---|---|---|
| 200 with existing label | Duplicate key, idempotent | Return the existing label |
| 409 Conflict | Duplicate detected | Re-query by reference; never re-create |
| 422 | Validation error | Fix the named field |
| 401/403 | Auth | Re-issue token; never retry |

Never issue a second `POST` with the same key. If the carrier returns 409,
query the label by the reference number first.

**Near-miss:** an agent sees 409 and treats it as "conflict = retry with a
new key". That creates a *second* label. 409 means: the key already exists,
find it, do not create.

## 4. Track via the official API only

- DHL: `GET /shipment/v2/tracking?shipmentNumber=<num>`
- DPD: `GET /track/{trackingNumber}` (JSON)
- GLS: `GET /track?trackingNumber=<num>` (SOAP or REST)
- Hermes: `GET /tracking?id=<num>`
- UPS: `GET /track?trackingNumber=<num>`

Cache results for 5 minutes (configurable). Never scrape the public tracking
page — it breaks on layout changes and violates the carrier's terms. The
`scripts/track.py` helper writes to a JSON cache file so the cache survives
restarts and is deterministic; a stale entry (older than the TTL) is re-pollled.

## 5. Reconcile

Compare, per label:
- `cost.amount` vs Ottili shipping record cost
- `status` vs Ottili shipping record status
- `trackingNumber` vs Ottili shipping record tracking number

On mismatch: re-query by tracking number, log the delta, flag for review.
On unknown result (timeout, partial): treat as unknown, re-query, log.
Exit codes: 0 = match, 1 = mismatch/unknown, 2 = malformed input.

## 6. Error → fix table

| Status | Meaning | Fix |
|---|---|---|
| 401/403 | Auth failure | Re-issue token; never retry with same token |
| 409 | Duplicate key | Re-query by reference; never re-create |
| 422 | Validation | Fix the named field in the body |
| 429 | Rate limit | Exponential backoff, max 3 attempts |
| 5xx | Outage | Backoff; mark label unknown |

## 7. Offline helper scripts

- `scripts/label_create.py` — builds the label request envelope per carrier
  with the idempotency key (dry-run by default; `--execute` sends).
- `scripts/track.py` — polls the official tracking endpoint (dry-run), with a
  disk-backed TTL cache; rejects non-numeric tracking numbers.
- `scripts/reconcile.py` — compares label cost/status/tracking with the Ottili
  shipping record and emits a delta report; `--strict` fails on missing fields.
