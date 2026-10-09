# SOURCES — carrier-apis-de

Retrieval date: 2026-10-09 (all URLs fetched with `curl` on that date unless
noted). Version-sensitive facts are pinned in `config/versions.json` and
never hardcoded in logic. Carriers update APIs without a public changelog —
re-verify against each developer portal before every build and record the
retrieval date here. Conflicts between sources are noted at the end.

## Primary sources (verified 2026-10-09)

| # | Source | URL | HTTP | Notes |
|---|---|---|---|---|
| 1 | DHL Parcel DE developer portal (API catalogue) | https://developer.dhl.com/ | 200 | Authoritative catalogue of DHL Post & Parcel Germany APIs. Retrieved 2026-10-09. The catalogue lists `dhl-parcel-de-private-shipping-post-parcel-germany`, `shipment-tracking`, `shipment-tracking-unified-push` and `authentication-api-post-parcel-germany`. |
| 2 | DHL Parcel DE — private shipping API reference | https://developer.dhl.com/api-reference/dhl-parcel-de-private-shipping-post-parcel-germany | 200 | Label creation, label access and tracking endpoints. Retrieved 2026-10-09. |
| 3 | DHL Parcel DE — shipment tracking API | https://developer.dhl.com/api-reference/shipment-tracking | 200 | Official tracking endpoint contract. Retrieved 2026-10-09. |
| 4 | DHL Parcel DE — authentication API | https://developer.dhl.com/api-reference/authentication-api-post-parcel-germany | 200 | OAuth2 token endpoint contract. Retrieved 2026-10-09. |
| 5 | DHL Parcel DE — Post & Parcel Germany hub | https://developer.dhl.com/post-and-parcel-germany | 200 | Service overview. Retrieved 2026-10-09. |
| 6 | DPD Germany — developing with DPD | https://www.dpd.com/de/developing-with-dpd | 200 | Developer portal entry point. Retrieved 2026-10-09. |
| 7 | DPD Germany — developer portal | https://www.dpd.com/de/developing-with-dpd/developer-portal | 200 | Label, tracking and webhook contracts. Retrieved 2026-10-09. |
| 8 | GLS Germany — developer area | https://gls-group.com/EN/shipping/developer-area | 200 | Label creation and tracking contracts. Retrieved 2026-10-09. |
| 9 | GLS Germany — tracking docs | https://gls-group.com/EN/shipping/developer-area/track | 200 | Tracking endpoint. Retrieved 2026-10-09. |
| 10 | GLS Germany — API docs | https://gls-group.com/EN/shipping/developer-area/api | 200 | API overview. Retrieved 2026-10-09. |
| 11 | UPS Germany — developer resources | https://www.ups.com/us/en/shipping/developer-resources.page | 200 | Label creation and tracking contracts. Retrieved 2026-10-09. |

## Hermes

- `https://www.hermes.com/en/developer` returned **403** at retrieval (2026-10-09) — the portal is not publicly crawlable. Hermes restricts API access to business customers; the access prerequisite is documented in the skill but the endpoint contract is **unverified** until a business-account holder confirms it. Treat Hermes facts as unverified.

## Version-sensitive notes

- **No carrier publishes a stable version page.** DHL, DPD, GLS, Hermes and UPS all change endpoints without a public changelog. The skill therefore pins confirmed versions in `config/versions.json` and marks them unverified until the carrier confirms. This is a known limitation, not a source conflict.
- **DHL API shape changed.** The previously cited `developer.dhl.com/api-reference/parcel-de` URL returns 404 (2026-10-09). The catalogue now lives at `developer.dhl.com/api-catalog` and the parcel API is under `post-and-parcel-germany`. Re-verify the exact label endpoint before every build.
- **Idempotency key names differ per carrier.** DHL uses `X-Request-ID`, UPS uses `X-Inbound-Idempotency-Key`, DPD/GLS/Hermes use a body reference field. The skill abstracts the key behind a per-carrier adapter; never assume one header name.
- **Sandbox availability:** DHL, DPD and UPS offer sandboxes; GLS and Hermes do not (Hermes requires a business account). Treat sandbox tests as optional.

## Conflicts / open questions

- The DHL catalogue URL changed between the 2026-10-07 and 2026-10-09 retrievals; the older `api-reference/parcel-de` path is stale and must not be cited.
- Hermes endpoint contract is unverified (403 at retrieval); flagged in the skill as a prerequisite.
- No public changelog exists for any carrier; re-verify on every build per the R3 rule.
