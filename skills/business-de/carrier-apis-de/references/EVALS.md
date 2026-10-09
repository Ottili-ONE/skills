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

## 6. The tracking cache has a stale entry. What do we do?

**Prompt:** "The tracking cache file has an entry older than 5 minutes. What do we do?"

**Expected behaviour:** Treat the entry as stale — re-poll the official endpoint. The cache TTL is 300 s (pinned in `config/versions.json`); a stale entry must never be served as fresh data. The `track.py` helper returns `cache_hit: false` and re-issues the request.

**Failure signs:** Serving a stale cached entry; hardcoding a TTL instead of reading it from config; ignoring the cache file entirely.

## 7. A tracking number is `ABC-DEF`. What happens?

**Prompt:** "A tracking number is `ABC-DEF`. What happens?"

**Expected behaviour:** The script rejects it before any request — `tracking number must be numeric`. Carrier tracking numbers are numeric; a non-numeric value is a data-entry error, not a carrier error, and must not be sent to the API.

**Failure signs:** Sending the malformed number to the API; treating the carrier's 4xx as the validation path.

## 8. Reconcile with `--strict`. What changes?

**Prompt:** "Reconcile with `--strict`. What changes?"

**Expected behaviour:** Strict mode fails on *missing* fields, not just mismatches. If either the label or the Ottili record lacks `cost`, `status` or `trackingNumber`, the report is non-ok (exit 1). Without `--strict`, missing fields are skipped. Use strict mode for audit-grade reconciliation.

**Failure signs:** Treating strict mode as a retry flag; returning ok when a field is absent.

## 9. Hermes has no public sandbox. How do we test?

**Prompt:** "Hermes has no public sandbox. How do we test the integration?"

**Expected behaviour:** Dry-run the request envelope with `label_create.py --carrier hermes --ref ORD-1` (no network). Verify the idempotency field is `correlationId` and it is embedded in the body, not a header. The Hermes endpoint contract is unverified (403 at retrieval) — flag it as a prerequisite for a business-account holder.

**Failure signs:** Skipping the idempotency check for Hermes; assuming a sandbox exists; hardcoding the Hermes endpoint.
