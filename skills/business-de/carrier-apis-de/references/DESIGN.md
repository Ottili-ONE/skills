# DESIGN: carrier-apis-de

## Trigger description (SKILL.md description draft, <=1024 chars)
"Integrate German carrier APIs (DHL, DPD, GLS, Hermes, UPS) for Ottili flows: create idempotent labels, track via official APIs only and reconcile label costs. Use when an agent must create a shipping label, track a shipment, or reconcile carrier API responses. Not for general shipping logic or unofficial tracking scrapers."

## Procedure outline
1. **Identify the carrier** — DHL (REST API), DPD (XML/JSON), GLS (SOAP/REST), Hermes (REST), UPS (REST). Each has a different auth and contract model.
2. **Use official APIs only** — never scrape tracking pages; every carrier has an official API and a contract; use it.
3. **Create idempotent labels** — every label request carries a client-generated Idempotency-Key; on a duplicate key, return the existing label, never create a second.
4. **Track** — poll the official tracking endpoint; cache results; never hammer the API.
5. **Reconcile** — compare label cost and status against the Ottili shipping record; on unknown result, re-query with the tracking number and log the reconciliation.
6. **Handle errors** — carrier error codes are mapped to a fix table; never retry auth errors.

## Scripts planned
- `scripts/label_create.py` — creates a label via the carrier API with an Idempotency-Key.
- `scripts/track.py` — polls the official tracking endpoint for a tracking number.
- `scripts/reconcile.py` — reconciles label cost/status with the Ottili shipping record.

## Five eval prompts
1. "Create a DHL label for a domestic parcel. What header proves it is idempotent?" -> must use an Idempotency-Key and return the existing label on a duplicate key.
2. "Track shipment 1234567890. Which endpoint do we call?" -> must name the official tracking endpoint for the carrier, never a web page.
3. "The label API returns error 409. What does it mean?" -> must name the conflict and the fix (duplicate key).
4. "Reconcile this label with our shipping record." -> must compare cost and status and report match/mismatch.
5. "Can we track via the carrier website instead of the API?" -> must say no and cite the official-API-only rule.

## What this skill does better than generic agents
- Encodes the Idempotency-Key rule explicitly, which generic agents skip and which causes double labels.
- Mandates official APIs only, which prevents scraping and tracking drift.
- Treats label reconciliation as a first-class step, not an afterthought.
