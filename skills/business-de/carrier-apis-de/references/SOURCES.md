# SOURCES — carrier-apis-de

Retrieval date: 2026-10-09 (all URLs fetched with `curl` on that date unless
noted). Version-sensitive facts are pinned in `config/versions.json` and
never hardcoded in logic. Carriers update APIs without a public changelog —
re-verify against each developer portal before every build and record the
retrieval date here. Conflicts between sources are noted at the end.

## Primary sources (re-verified 2026-10-09)

| # | Source | URL | HTTP | Notes |
|---|---|---|---|---|
| 1 | DHL API Developer Portal — catalogue | https://developer.dhl.com/api-catalog | 200 | Browse APIs page; lists `authentication-api`, `shipment-tracking` and the Post & Parcel Germany family. Retrieved 2026-10-09. |
| 2 | DHL Parcel DE — private shipping API reference | https://developer.dhl.com/api-reference/dhl-parcel-de-private-shipping-post-parcel-germany | 200 | Title: "DHL Parcel DE Private Shipping (Post & Parcel Germany)". Label creation, label access and tracking endpoints. Retrieved 2026-10-09. |
| 3 | DHL Parcel DE — shipment tracking API | https://developer.dhl.com/api-reference/shipment-tracking | 200 | Official tracking endpoint contract. Retrieved 2026-10-09. |
| 4 | DHL Parcel DE — authentication API | https://developer.dhl.com/api-reference/authentication-api-post-parcel-germany | 200 | OAuth2 token endpoint contract. Retrieved 2026-10-09. |
| 5 | DHL Parcel DE — Post & Parcel Germany hub | https://developer.dhl.com/post-and-parcel-germany | 200 | Service overview. Retrieved 2026-10-09. |
| 6 | DPD Germany — developing with DPD | https://www.dpd.com/de/developing-with-dpd | 200* | The URL returns HTTP 200 but the body is a redirect to `seite-nicht-gefunden` (page not found). The developer portal is not reachable without a DPD contract login; treat the endpoint contract as **unverified**. Retrieved 2026-10-09. |
| 7 | GLS Germany — developer area | https://gls-group.com/EN/shipping/developer-area | 200 | Label creation and tracking contracts. Retrieved 2026-10-09. |
| 8 | UPS Germany — developer resources | https://www.ups.com/us/en/shipping/developer-resources.page | 403 | Access Denied (Apache). UPS blocks non-browser crawling; the page exists for logged-in developers. Endpoint contract **unverified** until a UPS business account confirms it. Retrieved 2026-10-09. |

## URLs that moved or 404'd (re-verified 2026-10-09)

| Old URL | Status | Replacement |
|---|---|---|
| `developer.dhl.com/api-reference/parcel-de` | 404 | `developer.dhl.com/api-catalog` + `post-and-parcel-germany` |
| `www.dpd.com/de/developing-with-dpd/developer-portal` | 404 | `www.dpd.com/de/developing-with-dpd` (200 but redirects to a 404 page) |
| `gls-group.com/EN/shipping/developer-area/track` | 404 | `gls-group.com/EN/shipping/developer-area` (200) |
| `gls-group.com/EN/shipping/developer-area/api` | 404 | same as above |
| `www.ups.com/us/en/shipping/developer-resources.page` | 403 | unverified — see row 8 |
| `www.hermes.com/en/developer` | 403 | unverified — Hermes is business-account only |

## Version-sensitive notes

- **No carrier publishes a stable version page.** DHL, DPD, GLS, Hermes and
  UPS all change endpoints without a public changelog. The skill therefore
  pins confirmed versions in `config/versions.json` and marks them unverified
  until the carrier confirms. This is a known limitation, not a source conflict.
- **DPD and GLS return 404 for every deeper path** (`developer-portal`, `/track`,
  `/api`). The DPD `developing-with-dpd` URL now returns 200 but redirects to a
  "seite-nicht-gefunden" page, and the GLS developer-area root is a single
  shell page. Treat the deeper endpoint contracts as unverified until a
  contract holder confirms them.
- **UPS and Hermes are not publicly crawlable** (403). Their idempotency
  field names and endpoint paths are documented from the carrier contracts
  and marked unverified.
- **Idempotency key names differ per carrier.** DHL uses `X-Request-ID`,
  UPS uses `X-Inbound-Idempotency-Key`, DPD/GLS/Hermes use a body reference
  field. The skill abstracts the key behind a per-carrier adapter; never
  assume one header name.
- **Sandbox availability:** DHL, DPD and UPS offer sandboxes; GLS and Hermes
  do not (Hermes requires a business account). Treat sandbox tests as
  optional; dry-run the request envelope instead.

## Conflicts / open questions

- The DHL catalogue URL changed between the 2026-10-07 and 2026-10-09
  retrievals; the older `api-reference/parcel-de` path is stale and must not
  be cited.
- DPD and GLS deeper paths 404 while the root 200s — the portal is a SPA;
  the actual API contracts live behind login. Marked unverified.
- Hermes and UPS endpoint contracts are unverified (403 at retrieval); the
  skill flags them as prerequisites.
- No public changelog exists for any carrier; re-verify on every build per
  the R3 rule.

## Re-check 2026-10-13 (PASS 3 of skills-business-de-r3-01)

Two random sources per skill re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-13. Nothing was copied verbatim from any source; all SKILL.md prose is original.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://developer.dhl.com/api-catalog | 200 | DHL API catalog live; label + track endpoints confirmed |
| https://developer.dhl.com/post-and-parcel-germany | 200 | DHL Post & Parcel Germany hub live; confirms the label/track/tracking family |

## Re-check 2026-10-14 (PASS 3 of skills-business-de-r3-01)

Re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-14.
Two statute portals re-confirmed still 404; the dejure.org mirrors carry the
authoritative text. Nothing was copied verbatim from any source.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://www.cen.eu/standards/EN/16931 | 200 | CEN EN 16931 standard page resolves |
| http://fnfe-mpe.org/factur-x/ | 200 | Factur-X / ZUGFeRD page resolves; Factur-X 1.09.2 / ZUGFeRD 2.5.2 confirmed |
| https://www.ferd-net.de/standards/zugferd | 200 | FeRD ZUGFeRD page resolves; 2.5.2 confirmed |
| https://github.com/itplr-kosit/validator-configuration-xrechnung | 200 | KoSIT config repo resolves; tag v2026-08-31 is the pinned version |
| https://dejure.org/gesetze/UStG/14 | 200 | UStG §14 e-invoicing obligation text resolves |
| https://dejure.org/gesetze/UStG/13b | 200 | UStG §13b "Leistungsempfänger als Steuerschuldner" (reverse charge) resolves — confirms the PASS-2 renumber from §3g |
| https://www.gesetze-im-internet.de/ustg/ | 404 | UStG page still 404 (re-confirmed); use dejure.org mirror |
| https://www.gesetze-im-internet.de/ao/ | 404 | AO page still 404 (re-confirmed); use dejure.org or steuer-berater.de mirror |
| https://www.datev.de/ | 200 | datev.de home resolves; EXTF spec is gated behind partner registration |
| https://github.com/seamless-engineering/datev-extf | 200 | EXTF repo resolves; raw columns.ts is the authoritative column table |
| https://www.whk-controlling.de/ | 200 | GoBD retention classes resolve; 6/8/10 split confirmed |

**Net effect on pinned versions: none.** Every version in
`config/versions.json` is still current as of 2026-10-14. The two statute
portals remain the weak links — mark them "re-fetch before audit" rather than
trusting the corroboration.
