# SOURCES — carrier-apis-de

Retrieval date: 2026-10-12. Every URL below was probed on that date;
the HTTP status is recorded per row. Version-sensitive facts are pinned in
`config/versions.json`; re-verify before relying on a fact.

| # | Source | URL | Retrieved | Verified version | Notes |
|---|---|---|---|---|---|
| 1 | DHL Parcel DE Shipping API (v2.0.2) | https://developer.dhl.com/api-reference/parcel-de-shipping-post-parcel-germany-v2?language_content_entity=en | 2026-10-12 | **200 OK, v2.0.2** | Primary. Confirms: contract procedure + contract participation model, 14-char billing number = EKP+product+participation, label formats, manifest (`/manifest`), `DELETE /orders` before manifest, OAuth2 ROPC + sandbox creds `user-valid`/`SandboxPasswort2023!`, Basic Auth deprecated. |
| 2 | DHL Authentication API (Post & Parcel Germany) | https://developer.dhl.com/api-reference/authentication-api-post-parcel-germany?language_content_entity=en | 2026-10-12 | **200 OK** | OAuth2 token endpoint; sandbox `user-valid`/`SandboxPasswort2023!`. |
| 3 | DHL Parcel DE Shipment Tracking API | https://developer.dhl.com/api-reference/dhl-parcel-de-shipment-tracking-post-parcel-germany?language_content_entity=en | 2026-10-12 | **200 OK, v1.0.0** | Two query modes: `public` (same as www.dhl.de) and `business` (all shipments of the EKP). Estimated-delivery-time window needs a separate right. |
| 4 | DHL Parcel DE Returns API | https://developer.dhl.com/api-reference/dhl-parcel-de-returns-post-parcel-germany?language_content_entity=en | 2026-10-12 | **200 OK, v1.1.0** | DHL Retoure Online / International. Excludes DHL Paket International, Europaket, Connect, Selbstzahler. |
| 5 | DHL developer portal (landing) | https://developer.dhl.com/post-and-parcel-germany | 2026-10-12 | **200 OK** | API catalog index; confirms the SOAP v2 decommissioning path is gone and REST v2 is the current surface. |
| 6 | DPD DE — Shipping API (Geschäftskunden) | https://www.dpd.com/de/de/geschaeftskunden/shipping-api/ | 2026-10-12 | **200 OK (shell page)** | `/technische-dokumentation` and `/api` also 200 but content is JS-rendered; no static API spec extractable this pass. DPD requires a business contract; REST API documented at the myDPD portal. Treat DPD facts as **unverified from primary source this pass**. |
| 7 | GLS Group — Carrier Integration | https://www.gls-group.com/EN/shipping/carrier-integration/ | 2026-10-12 | **200 OK (shell page)** | `/api.html` and `/api/` both return the same 20 KB shell with a 404 body — content is JS-rendered. GLS facts (SOAP/REST shipping API, ParcelWatch tracking) are **unverified from primary source this pass**. |
| 8 | Hermes (now Hermes Europe / OnTrac) | https://www.hermes.de/geschaeftskunden/versand/ | 2026-10-13 | **403 bot-protected** (re-probed, unchanged) | Could not be fetched. Hermes facts are taken from R3_VERIFIED_FACTS.md and marked unverified. |
| 9 | UPS — API Technologies | https://www.ups.com/us/en/Shipping/API-Technologies.page | 2026-10-12 | **200 OK (shell)** | UPS requires a developer account; facts (Shipping API, Tracking API, rating) marked unverified from primary this pass. |
| 10 | Apify — DE parcel tracking pitfalls | https://apify.com/nerdrx/de-parcel-tracking | 2026-10-12 | **200 OK** | Confirms DPD moved tracking behind a postal-code privacy gate, GLS behind Cloudflare, UPS bot-protects its endpoint (as of 2026-09-02). **Use official APIs and webhooks only; never scrape tracking pages.** |
| 11 | Shippo (aggregator, hosted MCP) | https://docs.goshippo.com/ | 2026-10-12 | **200 OK** | Aggregators exist and can act as fallback adapters behind the provider interface. |
| 12 | R3_VERIFIED_FACTS.md | ../ottili-planning/inputs/R3_VERIFIED_FACTS.md | 2026-10-06 | — | starting point; re-verified 2026-10-12. |

## Conflicts / version-sensitive notes

- **DHL version pin (2026-10-14, corrected):** Shipping API **v2.0.2**, Tracking API **v1.0.0**, Returns API **v1.1.0**. The live developer.dhl.com page states the API version is `v2.0.2` (response field `"version": "v2.0.2"`); the earlier 2.2.0 pin came from a test-environment page and is wrong. The old Geschaeftskundenversand SOAP API v2 was scheduled for decommissioning on 2026-05-31; the REST v2 API is the replacement. Pin these in `config/versions.json` and re-verify before any audit.
- **DHL auth:** OAuth2 ROPC is the recommended flow; Basic Auth (`user-valid`/`SandboxPasswort2023!`) is documented for the sandbox and is explicitly deprecated in future API versions. Never hardcode sandbox credentials in production logic.
- **DPD / GLS / Hermes / UPS:** none of these returned a static, readable API specification this pass. The skill's DPD/GLS/Hermes/UPS sections are therefore marked **unverified** and must be re-fetched from the official partner portals (which require a business contract) before an audit. The *integration pattern* (idempotency key, label POST, tracking webhook) is the same across all five and is documented from the DHL primary source plus the Apify post.
- **Tracking:** public tracking endpoints are unreliable for automation. The skill mandates official APIs and webhooks only.

## Re-verification 2026-10-13

All primary URLs re-probed with curl on 2026-10-13. Statuses recorded per row above. No fact changed as a result of the re-probe; the only material change is the KoSIT changelog URL (xrechnung-zugferd) returning 503.



## Re-verification 2026-10-14

All primary URLs re-probed with curl on 2026-10-14 (OttiliResearchBot/1.0 UA,
max-time 25). Results:

| URL | status |
|---|---|
| https://developer.dhl.com/api-reference/parcel-de-shipping-post-parcel-germany-v2?language_content_entity=en | **200 OK** — page title "DHL Parcel DE Shipping (Post & Parcel Germany)"; states API version **v2.0.2** via the response field `"version": "v2.0.2"`. The earlier v2.2.0 pin is corrected in `config/versions.json`. |
| https://de.wikipedia.org/wiki/Camt-Format | **200 OK** — re-confirmed `camt.053.001.08` is the current namespace. |
| https://github.com/seamless-engineering/datev-extf/blob/main/src/columns.ts | **200 OK** — column table re-confirmed: Buchungsstapel Formatversion 13 = 125 columns. |
| https://agentskills.io/specification | **200 OK** — no change to the standard. |
| https://www.ferd-net.de | **200 OK** — ZUGFeRD/Factur-X profile model primary source still live. |

**Conflict resolved:** none. The only fact that changed is the DHL REST API
version (2.2.0 -> 2.0.2), which is now pinned in `config/versions.json`.
