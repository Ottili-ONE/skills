# DESIGN — problem-json-contracts

Status: draft v2 (2026-10-13). Supersedes the 24-line v1 that listed procedures without
pass/fail criteria. Trigger description, procedure, scripts and evals are all below.

## Trigger description (draft)
Use this skill when: designing or reviewing an HTTP API endpoint that returns errors; adding
a new error code to the catalogue; fixing a client that cannot parse error responses; writing
an SDK that must survive retry storms; or auditing an OpenAPI spec for error-drift.
Does NOT fire for: internal CLI tools with no HTTP transport, or logging libraries that emit
plain text (those are not problem documents).

## What it does better than existing public skills
Existing tools (openapi-generator, zod-to-openapi, Fastify error plugins, ogen) *generate* a
problem document but do not enforce the one-to-one mapping between the error catalogue and
the OpenAPI response table, nor do they pin retry semantics. Community agent skills for
"error handling" are generic prose. This skill ships `scripts/check_problem_catalogue.py`,
which fails CI on: duplicate codes, catalogue codes with no schema entry, schema entries with
no catalogue code, missing `retry_after` on retriable errors, and 5xx responses leaking
internal fields. It also embeds a ~60-line draft 2020-12 JSON Schema subset validator because
`jsonschema` is not installable on Biest (externally-managed environment). That is the gap no
public tool closes.

## Procedure outline
1. Pick the `type` URI form: absolute `https://<host>/prob/<code>` for public APIs,
   `about:<code>` for internal. Never reuse one `type` for two semantics.
2. Emit the six required fields on every response: `type`, `title`, `status` (int, == the
   HTTP code), `detail`, `instance` (URI). Optional: `trace_id`, `retry_after` (seconds),
   `errors` (field-level array).
3. Map status codes one-to-one: 4xx = client fault with a fix hint in `detail`; 5xx =
   server fault carrying `trace_id` only (never a stack trace or SQL text).
4. Retry semantics: `retry_after` on 429/503. Client backs off exponentially from 1 s, cap
   60 s, max 5 attempts, then surfaces with the `instance` URI for support lookup.
5. Maintain a single YAML catalogue. CI runs the checker so no duplicate codes exist and
   every code has a matching `$id` schema entry plus an `application/problem+json`
   declaration in the OpenAPI response table.

## Pass/fail checklist
- [ ] Every catalogue code appears exactly once (duplicate-key YAML silently keeps the last
      value — the checker detects this).
- [ ] Every catalogue code has a schema file under `--schema-dir` named `<code>.json`.
- [ ] Every schema `$id` maps back to a catalogue code (no orphan schemas).
- [ ] Every example's `status` field equals its catalogue status (a lying `status` is the
      #1 client-parse failure).
- [ ] Every retriable code (429, 503) carries `retry_after` in its example.
- [ ] Every OpenAPI response entry for a problem code declares `application/problem+json`.
- [ ] No 5xx example contains `stack_trace`, `sql`, or internal hostnames.
- [ ] Exactly one HTTP status per catalogue entry; two entries may share a status only if
      their `type` URIs differ.

## Scripts (shipped)
- `scripts/check_problem_catalogue.py` — reads `catalogue.json` + `openapi.yaml` +
  `--schema-dir`. Exit 0 on match, 1 on drift, 2 on malformed input. Self-contained (embedded
  schema subset validator). Args: `--catalogue`, `--openapi`, `--schema-dir`.
- Examples in `references/examples/`: `good/` (catalogue + openapi + 4 schema/example pairs),
  `bad/duplicate_code` (also the malformed duplicate-key fixture, `duplicate_code.yaml`),
  `bad/missing_openapi_response`, `bad/missing_problem_json`,
  `bad/retryable_without_retry_after`, `bad/missing_schema_file`, `bad/example_fails_schema`.
- Self-test: `scripts/check_problem_catalogue_test.py` (1 good, 6 bad, 1 malformed).

## Five eval prompts
1. "My API returns `{"error": "user not found"}` on 404. Is it RFC 9457 compliant?" → No.
   Missing `type`, `title`, `status`, `detail`, `instance`; `error` is not a valid field name.
2. "I added a new code `INTERNAL_TIMEOUT` with status 504. What must I do?" → Add it to the
   catalogue, add a `$id` schema entry, declare `application/problem+json` in the OpenAPI 504
   response, include `trace_id`, no `detail` with internals.
3. "A client retries a 429 without reading `retry_after` and hammers us. What's wrong?" →
   The client ignored `retry_after`; it must back off exponentially from 1 s, cap 60 s,
   max 5 attempts.
4. "My 500 response includes `stack_trace`. Is that allowed?" → No. 5xx carries `trace_id`
   only; log the stack trace server-side.
5. "I have two catalogue entries with status 409 — one for a version conflict, one for a
   duplicate key. Is that a problem?" → Yes if they share a `type`. Give each a distinct
   `type` URI; prefer distinct statuses (409 vs 400).

## Known pitfalls (from incidents)
- YAML duplicate keys are silently dropped by most parsers; the checker explicitly re-reads
  the raw file for duplicate keys.
- `yaml.safe_load` is used, not `yaml.full_load`, so a `$id` containing a tab is rejected.
- A schema file present but with a wrong `$id` looks like a match; the checker compares the
  `$id` to the catalogue code, not just the filename.
