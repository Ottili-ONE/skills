# EVALS — carrier-apis-de

Each prompt lists the expected behaviour and the failure signs an agent must
watch for.

## 1. Idempotency
**Prompt:** "Create two DHL labels with the same `clientReferenceNo`. What
should happen?"

**Expected behaviour:** The second call returns the **same** label/shipment
number, not a duplicate. Retry with the same key; never generate a new one.

**Failure signs:** Two different shipment numbers for one order; a new
`clientReferenceNo` on retry.

## 2. Manifest lock
**Prompt:** "A shipment was manifested. Can I edit its address?"

**Expected behaviour:** No. `DELETE /orders` is also blocked post-manifest;
recreate before manifest. A manifested shipment cannot be edited.

**Failure signs:** Silently PATCHing a manifested shipment; assuming the edit
went through.

## 3. Unknown tracking number
**Prompt:** "Track `12345678901234567890`."

**Expected behaviour:** Exit non-zero with a structured "unknown" error, not a
scraped HTML page. Use the official Tracking API only.

**Failure signs:** Scraping www.dhl.de; returning a 200 with no data.

## 4. Scraping ban
**Prompt:** "The DPD tracking page shows a privacy gate for my postal code.
Can I scrape around it?"

**Expected behaviour:** No — use the official DPD API or webhook. DPD moved
tracking behind a postal-code privacy gate, GLS behind Cloudflare, UPS
bot-protects its endpoint (Apify, verified 2026-09-02).

**Failure signs:** Attempting a GET on the public tracking URL.

## 5. Reconciliation gap
**Prompt:** "The carrier charged EUR 4.95 but the ledger has no matching
order."

**Expected behaviour:** Flag as `unknown_result`, do not write off. Match by
`clientReferenceNo`; escalate a charge with no ledger entry.

**Failure signs:** Auto-allocating to "shipping expense"; marking it matched
without a ledger entry.

## Near-miss triggers

### N1. "The label POST returned 201, so the shipment exists"
**Trap:** a 201 is not proof the shipment is manifestable. Check the manifest
state before any edit; recreate before manifest if it is closed.

### N2. "I will scrape the tracking page for the status"
**Trap:** DPD privacy gate, GLS Cloudflare, UPS bot-protection (Apify,
verified 2026-09-02). Use official APIs and webhooks only.

### N3. "DPD and DHL use the same API"
**Trap:** DPD/GLS/Hermes/UPS specs are unverified this pass. Document the
common pattern (idempotency key, label POST, tracking webhook) but flag every
carrier-specific fact as unverified until re-fetched from the partner portal.
