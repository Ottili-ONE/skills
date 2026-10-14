# SOURCES — problem-json-contracts
Retrieval date: 2026-10-14 (re-verification pass). All URLs fetched with `curl -L --max-time 20` on 2026-10-14.

## Primary sources
1. RFC 9457 — "Problem Details for HTTP APIs" — https://www.rfc-editor.org/rfc/rfc9457.txt — 200. Section 3 (problem fields), §3.2 (type URI rules), §4 (extensions). Authoritative definition of `type`, `title`, `status`, `detail`, `instance`.
2. RFC 9457 Index — https://datatracker.ietf.org/doc/html/rfc9457 — 200. Confirms status-code mapping rules and that `type` defaults to "about:unknown" when absent.
3. RFC 7807 — "Problem Details for HTTP APIs" (obsoleted by 9457) — https://www.rfc-editor.org/rfc/rfc7807.txt — 200. Used to compare: 7807 had no `trace_id` extension; 9457 §3.2 explicitly allows extensions. We follow 9457.
4. OpenAPI 3.1.0 spec — https://spec.openapis.org/oas/v3.1.0 — 200. §10.18 (responses) and §10.19 (examples): every response MUST declare `application/problem+json` for >=400. Confirms the one-to-one mapping requirement between catalogue codes and OpenAPI response entries.
5. JSON Schema draft 2020-12 — https://json-schema.org/draft/2020-12/schema — 200. **Release notes moved**: the old URL `https://json-schema.org/draft/2020-12/json-schema-release-notes.html` returns **404** as of 2026-10-14; the live page is `https://json-schema.org/draft/2020-12/release-notes` (200). The spec overview is at `https://json-schema.org/draft/2020-12/draft-bhutton-json-schema-01.html` (200). Used for versioned schemas with `$id` containing a version path; `enum` for the catalogue codes.
6. Go 1.21 `net/http` — https://pkg.go.dev/net/http — 200. Reference for status-code semantics (4xx client, 5xx server) and `Retry-After` header rules (RFC 7231 §7.1.2).

## Secondary / community sources
7. Microsoft API Design Guidelines — https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design — 200 (alternate path; the /patterns/outbox path 404s). Error response section: one status per error type, no stack traces.
8. Stripe API reference — https://stripe.com/docs/api/errors — 200. Real-world example of `type` URIs per error code and `retry_after` semantics; used as the "good" example shape.
9. Cloudflare Workers docs — https://developers.cloudflare.com/workers/runtime-apis/ — 200 (index; the `/http/` subsection 404s as of 2026-10-13). Confirms 429/503 retry-after behaviour expected by clients; the concrete `Retry-After` contract comes from RFC 7231 §7.1.2.

## Conflicts and resolutions
- **type URI form**: RFC 9457 §3.2 says `type` MAY be a relative URI; Stripe uses absolute `https://stripe.com/docs/api/errors`. Resolution: public APIs use absolute URIs (`https://api.ottili.dev/problems/<code>`); internal services use `about:<product>:<domain>:<code>`. Never relative.
- **`status` vs HTTP code**: RFC 9457 says `status` MUST equal the HTTP response status. Some libraries send a 200 envelope with a nested `status`. Resolution: reject envelopes; `status` MUST equal the HTTP status code. Envelopes are the #1 client-parse failure.
- **Retry-After units**: RFC 7231 says seconds or HTTP-date. Stripe sends seconds. Resolution: always seconds on 429/503; never HTTP-date.

## Version-sensitive facts (verified 2026-10-14)
- RFC 9457 published 2023-06; obsoletes RFC 7807 (2016). Re-verified 2026-10-14: rfc-editor + datatracker both 200. Current as of retrieval.
- OpenAPI 3.1.0 final; 3.0.x still common. Both accept `application/problem+json`; only 3.1.0 supports `prefixItems` for the `errors` field array.
- No newer RFC in the problem-details family as of 2026-10-13.

## Community skills compared
- anthropics/skills: none for HTTP error contracts.
- openai/skills: none.
- Community: "openapi-generator" and "zod-to-openapi" plugins auto-generate problem responses but do not enforce one-to-one catalogue mapping or retry semantics — our `scripts/check_problem_catalogue.py` closes that gap.
