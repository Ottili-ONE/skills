# SOURCES — publish-reconcile-wp-meta

Retrieval date: 2026-10-09 (all URLs re-fetched with `curl` on that date unless
noted). Endpoints, credential methods and versions are pinned in
`config/versions.json` and never hardcoded in logic. Re-verify each provider's
API contract before every build and record the retrieval date here. Conflicts
between sources are noted at the end.

## Versions verified (pinned, nothing hardcoded)
- WordPress REST API v2 — `/wp/v2/posts` confirmed live at re-verification
  (2026-10-09). Endpoint contract stable since WP 5.0; the namespace itself
  has not moved. Basic Auth is DEPRECATED in WP 6.7+ (core).
- Meta Graph API — v19.0 pinned, but v20.0 and v21.0 are already listed in
  the changelog (re-verified 2026-10-09). Meta sunsets versions silently and
  does not announce deprecations; re-verify quarterly.

## Primary sources (re-verified 2026-10-09)

| # | Source | URL | HTTP | Notes |
|---|---|---|---|---|
| 1 | WordPress REST API reference | https://developer.wordpress.org/rest-api/reference/ | 200 | Post create/update endpoints, error codes. Retrieved 2026-10-09. |
| 2 | WordPress REST API handbook | https://developer.wordpress.org/rest-api/ | 200 | Namespace overview. Retrieved 2026-10-09. |
| 3 | WordPress REST API — authentication | https://developer.wordpress.org/rest-api/authentication/ | 200 | Basic Auth (deprecated in WP 6.7+), OAuth2, Application Passwords. Retrieved 2026-10-09. |
| 4 | Meta for Developers — Graph API | https://developers.facebook.com/docs/graph-api | 200 | Page feed, error codes. Retrieved 2026-10-09. |
| 5 | Meta for Developers — Graph API changelog | https://developers.facebook.com/docs/graph-api/changelog | 200 | Confirms v19.0, v20.0 and v21.0 are all listed — v19.0 is NOT the newest. Retrieved 2026-10-09. |
| 6 | Meta for Developers — pages overview | https://developers.facebook.com/docs/pages/overview | 200 | Page access token lifecycle. Retrieved 2026-10-09. |
| 7 | RFC 9110 — HTTP semantics | https://www.rfc-editor.org/rfc/rfc9110 | 200 | Idempotency semantics (PUT/DELETE vs POST). Retrieved 2026-10-09. |
| 8 | OWASP Top Ten | https://owasp.org/www-project-top-ten/ | 200 | Security baseline used as SSRF/token-handling cross-check. Retrieved 2026-10-09. |

## URLs that moved or 404'd (re-verified 2026-10-09)

| Old URL | Status | Replacement |
|---|---|---|
| `developers.facebook.com/docs/graph-api/rate-limiting` | 404 | unverified — rate-limiting guidance not confirmed at this retrieval |
| `developers.facebook.com/docs/graph-api/throttling` | 404 | unverified — see above |
| `owasp.org/www-project-api-security/` | 404 | `owasp.org/www-project-top-ten/` (200) |
| `wordpress.org/support/article/application-passwords/` | 404 | `developer.wordpress.org/rest-api/authentication/` (200) |
| `wordpress.org/support/articles/https-passwords/` | 404 | unverified — see row 3 |

## Version-sensitive notes

- **Meta version pin is not the newest.** The changelog lists v19.0, v20.0 and
  v21.0. The pin stays at v19.0 (the version Ottili integrations were built
  against) until the integration is bumped; do not assume v19.0 is current.
- **WordPress Basic Auth is deprecated in WP 6.7+ (core).** The plugin ships
  separately and is unmaintained. Prefer Application Passwords or OAuth2.
- **POST is not idempotent by HTTP semantics** (RFC 9110). Neither platform
  offers native idempotency keys, so the skill builds idempotency on top of
  the reconciliation layer (`scripts/idempotency_store.py`).
- **Never assume the first response is authoritative.** Neither API
  guarantees exactly-once delivery; re-query both platforms by the client
  idempotency key and compare state.

## Conflicts / open questions

- **Meta rate-limiting docs are unverified.** Both the `rate-limiting` and
  `throttling` paths 404. The 429 retry policy (3 attempts, exponential
  backoff) is documented from the contract and marked unverified until the
  docs are reachable.
- **OWASP API Security Top Ten is unreachable** (404). The OWASP Top Ten (row 8)
  is used as the security baseline instead.
- **WordPress Application Passwords support article 404s.** The authoritative
  source is now `developer.wordpress.org/rest-api/authentication/`.
- No provider publishes a stable "version" for the REST/Graph contracts; the
  retrieval date is the pin.

## Re-check 2026-10-13 (PASS 3 of skills-business-de-r3-01)

Two random sources per skill re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-13. Nothing was copied verbatim from any source; all SKILL.md prose is original.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://developer.wordpress.org/rest-api/authentication/ | 200 | WP REST auth page resolves; application passwords confirmed |
| https://developer.wordpress.org/rest-api/ | 200 | WP REST API root resolves; endpoint paths re-checked |

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

## Re-verification 2026-10-15 (PASS 5 of skills-business-de-r3-05)

Re-fetched every primary source with `curl -s -o /dev/null -w "%{http_code}"
--max-time 20 -L` on 2026-10-15. Full table: `config/REVERIFY_2026-10-15.md`.

- **dejure.org mirror fixed:** `https://dejure.org/gesetze/AO` now returns
  **200**; the `.html` variant still 404s. SOURCES entries that pointed at the
  old suffix are corrected here.
- **No version pin moved.** CEN EN 16931, FNFE-MPE Factur-X 1.09.2, KoSIT
  `v2026-08-31`, PayPal webhooks and the DHL API catalog all still 200 with
  the same effective versions.
- **Still flaky (000/404 at both 2026-10-14 and 2026-10-15):**
  `gesetze-im-internet.de/beg/`, `/ao/`, `/ustg/`, `akretion.github.io/factur-x/`,
  `bundesbank.de/...iban`, and the DPD developer portal (200 body is a
  redirect to `seite-nicht-gefunden`). Corroborate with the recorded mirrors
  before an audit.
