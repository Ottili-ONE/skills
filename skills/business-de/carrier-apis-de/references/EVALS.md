# EVALS — carrier-apis-de

Each prompt lists the expected behaviour and the failure signs an agent must
watch for. The offline scripts (`scripts/label_create.py`, `scripts/track.py`,
`scripts/reconcile.py`) are run in dry-run mode and their output compared to
the expected behaviour. Tests live in `tests/test_carrier.py`.

## 1. Create a DHL label for a domestic parcel. What header proves it is idempotent?

**Prompt:** "Create a DHL label for a domestic parcel. What header proves it is idempotent?"

**Expected behaviour:** The request carries the client-generated idempotency
key in the `X-Request-ID` header. On a duplicate key the carrier returns the
existing label — never create a second. The script output shows
`idempotency_field: X-Request-ID` and the header is set on the request.

**Failure signs:** Using a different header name for DHL; creating a second
label on retry without the key; treating a 409 as a reason to re-create.

## 2. Track shipment 12345678901234567890. Which endpoint do we call?

**Prompt:** "Track shipment 12345678901234567890. Which endpoint do we call?"

**Expected behaviour:** Name the official tracking endpoint for the carrier
(`/shipment/v2/tracking?shipmentNumber=` for DHL, `/track/` for DPD, etc.),
never a web page. Cache results for 5 minutes. The script output shows
`endpoint_path` and `cache_ttl_seconds: 300`.

**Failure signs:** Suggesting the public tracking page; omitting the cache TTL;
naming a non-existent endpoint.

## 3. The label API returns error 409. What does it mean?

**Prompt:** "The label API returns error 409. What does it mean?"

**Expected behaviour:** 409 means conflict / duplicate key. The fix is to
re-query by the reference number and return the existing label — never
re-create. Auth errors (401/403) must never be retried with the same token.

**Failure signs:** Retrying the POST with the same key; treating 409 as a
validation error; retrying a 401.

## 4. Reconcile this label with our shipping record.

**Prompt:** "Reconcile this label with our shipping record."

**Expected behaviour:** Compare `cost`, `status` and `trackingNumber` between
the carrier label and the Ottili shipping record. Emit a delta report; return
exit 0 on match, exit 1 on mismatch. On an unknown result (timeout, partial),
re-query by tracking number and log the delta.

**Failure signs:** Comparing only one field; returning ok on a mismatch;
failing to re-query on an unknown result.

## 5. Can we track via the carrier website instead of the API?

**Prompt:** "Can we track via the carrier website instead of the API?"

**Expected behaviour:** No. Every carrier has an official tracking API; scraping
the public page breaks on layout changes and violates the carrier's terms.
Use the official endpoint and cache results.

**Failure signs:** Recommending a web scraper; citing the tracking page as a
source of truth; omitting the caching rule.
