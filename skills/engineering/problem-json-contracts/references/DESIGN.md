# DESIGN — problem-json-contracts

## Trigger description (draft)
"Use this skill when you are designing or reviewing an HTTP API endpoint that returns errors, adding a new error code, fixing a client that cannot parse error responses, or writing an SDK that must survive retry storms. Do not use for internal CLI tools with no HTTP transport."

## What it does better than existing public skills
Existing tools (openapi-generator, zod-to-openapi, Fastify error plugins) generate *a* problem document. They do not enforce the one-to-one mapping between the error catalogue and the OpenAPI response table, nor do they pin retry semantics. This skill ships `scripts/check_problem_catalogue.py`, which fails CI on: duplicate codes, catalogue codes with no schema entry, schema entries with no catalogue code, missing `retry_after` on retriable errors, and 5xx responses leaking internal fields. That is the gap no public tool closes.

## Procedure outline
1. Pick the `type` URI form (absolute for public, `about:` for internal). Never reuse a type for two semantics.
2. Emit the six required fields: `type`, `title`, `status` (int, == HTTP code), `detail`, `instance` (URI). Optional: `trace_id`, `retry_after`, `errors` (field-level array).
3. Map status codes: 4xx = client fault with fix hint; 5xx = server fault with `trace_id` only. Exactly one status per catalogue entry.
4. Retry semantics: `retry_after` (seconds) on 429/503; client backs off exponentially from 1 s, cap 60 s, max 5 attempts, then surface with the `instance` URI for support lookup.
5. Maintain a single YAML catalogue; CI runs the checker so no duplicate codes and every code has a matching schema entry.

## Scripts (shipped)
- `scripts/check_problem_catalogue.py` — reads `catalogue.yaml` + `openapi.yaml`, exits 0 on match, 1 on drift, 2 on malformed input. Args: `--catalogue`, `--openapi`, `--schema-dir`. Examples in `examples/` (catalogue.json, openapi.yaml, schemas) run green.

## Five eval prompts
1. "My API returns `{"error": "user not found"}` on 404. Is it RFC 9457 compliant?" → No. Missing `type`, `title`, `status`, `detail`, `instance`; `error` is not a valid field name.
2. "I added a new code `INTERNAL_TIMEOUT` with status 504. What must I do?" → Add it to the catalogue YAML, add a `$id` schema entry, declare `application/problem+json` in the OpenAPI 504 response, include `trace_id`, no `detail` with internals.
3. "A client retries a 429 without reading `retry_after` and hammers us. What's wrong?" → The client ignored `retry_after`; it must back off exponentially starting at 1 s, cap 60 s, max 5 attempts.
4. "My 500 response includes `stack_trace`. Is that allowed?" → No. 5xx must carry `trace_id` only; log the stack trace server-side.
5. "I have two catalogue entries with status 409 — one for a version conflict, one for a duplicate key. Is that a problem?" → Yes. One status per type; give each a distinct `type` URI and a distinct HTTP status if possible (409 vs 400).
