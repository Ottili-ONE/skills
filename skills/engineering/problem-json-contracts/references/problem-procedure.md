# Problem JSON Contracts — Full Procedure
Retrieval date: 2026-10-12. Primary: RFC 9457 (2023), obsoletes RFC 7807 (2016).

## 1. Type URI policy
| Scope | Form | Example |
|-------|------|---------|
| Public API | `https://api.ottili.dev/problems/<code>` | `https://api.ottili.dev/problems/user-not-found` |
| Internal service | `about:<product>:<domain>:<code>` | `about:ottili:users:not-found` |
| Unknown | `about:unknown` | only when the type genuinely cannot be enumerated |

Never use a bare string, never a relative URI, never reuse one type for two semantics.

## 2. Required and optional fields
Required: `type` (URI), `title` (string, <= 120 chars), `status` (int, MUST equal the HTTP response status), `detail` (string, <= 500 chars), `instance` (URI identifying the specific occurrence).
Optional extensions: `trace_id` (string, on 5xx), `retry_after` (int seconds, on 429/503), `errors` (array of field-level objects with `field`, `code`, `message`).

All strings UTF-8. No stack traces, no connection strings, no SQL in `detail` on 5xx.

## 3. Status code mapping
- 4xx: client fault. `detail` may include a fix hint. `instance` may include the offending resource.
- 5xx: server fault. `detail` is generic ("internal error"); the actionable field is `trace_id`. Log internals server-side.
- Exactly one HTTP status per catalogue entry. If two distinct errors share a status, give them distinct `type` URIs and, where possible, distinct statuses.

## 4. Retry semantics
- Emit `retry_after` (integer seconds) on every retriable error: 429, 503, 504, and any 5xx marked `retryable: true` in the catalogue.
- Client contract: exponential backoff starting at 1 s, doubling each attempt, capped at 60 s, maximum 5 attempts. After the 5th failure, surface the error to the user with the `instance` URI for support lookup.
- Preserve the idempotency-key header across retries (see outbox-idempotency).

## 5. Error catalogue
Single YAML file, one entry per code:
```yaml
codes:
  user-not-found:
    status: 404
    title: "User not found"
    retryable: false
  rate-limit-exceeded:
    status: 429
    title: "Rate limit exceeded"
    retryable: true
    retry_after: 60
```
CI runs `scripts/check_problem_catalogue.py` against the catalogue + OpenAPI spec + JSON Schema dir. It fails on: duplicate codes, catalogue code without an OpenAPI response entry, OpenAPI >=400 response without `application/problem+json`, or schema `enum` not matching the catalogue keys exactly.

## 6. Versioned schemas
Each schema carries `$id` with a version path, e.g. `https://api.ottili.dev/schemas/v1/user-not-found.json`. Never break an existing `$id`; add a new version instead. The `errors` array uses `prefixItems` (OpenAPI 3.1.0) or `items` (3.0.x).

## Worked examples
Good:
```json
{ "type": "https://api.ottili.dev/problems/user-not-found",
  "title": "User not found",
  "status": 404,
  "detail": "No user with id 42.",
  "instance": "/users/42",
  "trace_id": "abc123" }
```
Bad (envelope):
```json
{ "status": 404, "detail": "No user with id 42." }
```
Bad (5xx leakage):
```json
{ "type": "about:ottili:db:connection", "status": 503,
  "detail": "connection refused at 10.0.0.5:5432", "trace_id": "abc" }
```

## Verification checklist
- [ ] Every endpoint returns `application/problem+json` on >=400.
- [ ] Catalogue YAML has no duplicate codes.
- [ ] Schema validates all examples in `references/examples/`.
- [ ] `retry_after` present on all retriable errors.
- [ ] No internal fields leaked on 5xx responses.
- [ ] `scripts/check_problem_catalogue.py` passes in CI.
