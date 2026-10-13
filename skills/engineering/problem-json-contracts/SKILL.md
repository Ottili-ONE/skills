---
name: problem-json-contracts
description: "RFC 9457 problem+json error contracts for Ottili APIs: error catalogue, retry semantics, versioned schemas, and validators that fail on malformed or non-idempotent error responses. Use when designing an HTTP API endpoint that returns errors, adding an error code, or investigating 'client cannot parse the error' / 'retry loop hammered us' incidents."
license: MIT-compat
compatibility: "Any HTTP API; RFC 9457 (2023); JSON Schema draft 2020-12"
metadata: {}
allowed-tools: []
---
# Problem JSON Contracts Skill — Quick Reference (body <500 lines; full procedure in references/problem-procedure.md)

## When to use this skill (trigger)
Any of these fires it:
- Designing an HTTP API endpoint that returns errors.
- A migration adds a new error code or changes a field name in an error response.
- An incident report says "client cannot parse the error" or "retry loop hammered us".
- Code review mentions `{"error": "..."}` without type/instance/status fields.
- Adding a new language SDK and needing stable error shapes.

## When NOT to use this skill
- Internal CLI-only tools with no HTTP transport.
- Health-check endpoints that return plain text 200.

## Decision table — error shape
| Pattern | When to pick | Pitfall |
|---------|-------------|---------|
| RFC 9457 `application/problem+json` with type URI | Default for all public HTTP APIs | `type` must be an absolute URI; use `about:` or `urn:` for internal codes |
| Versioned JSON Schema (`$id` with version path) | Multiple client versions in the wild | Never break existing `$id`; add a new schema version instead |
| Error catalogue enum (machine code + human message) | Every error must be machine-searchable by ops | Do not put stack traces in the catalogue response; log separately |

## Near-miss triggers (act before the incident)
- An endpoint returns a 200 envelope with a nested `status` → the #1 client-parse failure; reject envelopes.
- `type` is a bare string or a relative URI → clients cannot resolve it; require an absolute URI.
- A 5xx response leaks connection strings or SQL in `detail` → replace with `trace_id` only.
- `retry_after` is missing on 429/503 → clients hammer the server; emit seconds, never HTTP-date.
- Two catalogue entries share one `type` URI → silently conflates two semantics; one type per meaning.
- A catalogue code has no OpenAPI response entry → CI must fail (`scripts/check_problem_catalogue.py`).

## Numbered procedure (summary; full recipe in references/problem-procedure.md)
1. **Pick type URI** — `about:<product>:<domain>:<code>` for internal; `https://api.ottili.dev/problems/<code>` for public. Never reuse a type for two different semantics.
2. **Required fields**: `type`, `title`, `status` (int), `detail`, `instance` (URI). Optional: `trace_id`, `retry_after`, `errors` (field-level array). All strings UTF-8, max lengths enforced by schema (`title` <= 120, `detail` <= 500).
3. **Status code mapping**: 4xx = client fault with fix hint; 5xx = server fault with trace_id only; never leak internals on 5xx. Map exactly one status per type — no overlap between catalogue entries.
4. **Retry semantics**: include `retry_after` (seconds) on 429/503; idempotency-key header preserved across retries; client MUST back off exponentially starting at 1s, cap at 60s, max 5 attempts then surface to user with instance URI for support lookup.
5. **Error catalogue**: single YAML file listing every code, its status, title template, and retryability flag; CI runs `scripts/check_problem_catalogue.py` against it so no duplicate codes and every code has a schema entry matching the catalogue enum value exactly one-to-one with OpenAPI operation responses.

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

## Pitfalls from research
- Envelopes with a nested `status` are the #1 client-parse failure; `status` MUST equal the HTTP status code.
- `type` as a relative URI is unresolvable; public APIs use absolute URIs, internal services use `about:`.
- Stack traces and connection strings in `detail` on 5xx are a data-leak incident; use `trace_id` only.
- `retry_after` in HTTP-date format is ignored by most clients; always use integer seconds.
- Reusing one `type` URI for two different semantics conflates them; one type per meaning.

## Verification checklist (all must pass before merge)
- [ ] Every endpoint returns `application/problem+json` on >=400
- [ ] Catalogue YAML has no duplicate codes
- [ ] Schema validates all examples in `examples/`
- [ ] `retry_after` present on all retriable errors
- [ ] No internal fields leaked on 5xx responses
- [ ] `scripts/check_problem_catalogue.py` passes in CI

## Related skills
- [pg-rls-multitenant](../pg-rls-multitenant/SKILL.md)
- [outbox-idempotency](../outbox-idempotency/SKILL.md)
