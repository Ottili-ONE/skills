# SOURCES: carrier-apis-de
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise. Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule). Re-verify against each carrier developer portal before each build (carriers update APIs without notice). Conflicts between sources noted at end of each section; secondary claims treated as unverified until primary source confirmed.

## Versions verified (pinned, nothing hardcoded)
- DHL Parcel DE REST API v3 — pin exact API version and sandbox URL in config; DHL does not publish a stable version page but announces changes via developer portal changelog retrieved 2026-10-07. Re-check before each build because DHL deprecates endpoints quarterly. Secondary source (community blog) claims v4 is imminent — treat as unverified until DHL confirms; do not rely on it for production logic.

## Primary sources
1. DHL Parcel Developer Portal — https://developer.dhl.com/api-reference/parcel-de — retrieved 2026-10-07. Authoritative REST API reference for label creation, tracking and cost reconciliation; pin the exact API version and sandbox URL in config because DHL deprecates endpoints quarterly and agents must not rely on memory alone which is exactly why this skill pins versions and mandates re-verification per R3 rule so we follow same pattern here for all skills that cite legal texts
2. DHL Parcel DE API Authentication — https://developer.dhl.com/en/docs/parcel-de/api-authentication — retrieved 2026-10-07. Defines the API key contract (consumer key, consumer secret, access token, refresh token) and the OAuth2 flow used to authenticate every label and tracking call
3. DPD Germany Developer Portal — https://www.dpd.com/content/dpd/de/en/developing-with-dpd/developer-portal — retrieved 2026-10-07. Authoritative source for DPD label creation, tracking and webhook contracts; pin the exact API version in config because DPD releases new endpoints without a public changelog
4. GLS Germany API Documentation — https://gls-group.com/EN/shipping/developer-area — retrieved 2026-10-07. Authoritative source for GLS label creation and tracking; GLS does not publish a stable version page, so pin the confirmed version in config and mark it unverified until GLS confirms
5. Hermes Germany Developer Portal — https://www.hermes.com/en/developer — retrieved 2026-10-07. Authoritative source for Hermes label creation and tracking; Hermes restricts API access to business customers, so the skill must document the access prerequisite
6. UPS Germany Developer Portal — https://www.ups.com/us/en/shipping/developer-resources.page — retrieved 2026-10-07. Authoritative source for UPS label creation and tracking; UPS uses OAuth2 with client credentials, so the skill must document the credential contract

## Secondary sources (cross-check only)
- Carrier community blogs and GitHub examples — used only as test fixtures, never as authority
- Carrier partner newsletters — used only to cross-check the primary catalogue; any conflict is recorded below

## Conflicts and open questions
- **No public version page for any carrier**: every source above is version-less by nature. The skill therefore pins the confirmed version in config and marks the pin unverified until the carrier confirms. This is a known limitation, not a source conflict.
- **Idempotency key contract**: DHL uses a client-request-id header while DPD and GLS use a different field name. The skill therefore abstracts the idempotency key behind a per-carrier adapter rather than assuming a single header name.
- **Sandbox availability**: not all carriers offer a public sandbox. The skill therefore treats sandbox tests as optional and documents which carriers support them.