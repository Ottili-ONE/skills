# EVALS — problem-json-contracts
Retrieval date: 2026-10-13. Verified versions: RFC 9457 (2023, obsoletes 7807);
JSON Schema draft 2020-12. Sources: references/SOURCES.md.

Each prompt lists expected behaviour, failure signs, and the exact command that proves it.

## E1 — envelope detection
**Prompt**: "My endpoint returns `{"status": 404, "detail": "missing"}` with HTTP 200.
Is this acceptable?"
**Expected**: no — the HTTP status must be 404 and the `status` field must equal it.
**Failure sign**: agent accepts the envelope.
**What the skill changes vs no skill**: without the skill an agent ships `{"status": 404}` behind HTTP 200 and every client has to guess the real status from the body. The skill makes the HTTP status the machine-readable signal and requires the body `status` to equal it, so a lying envelope is a defect, not a quirk.
**Exact command to verify**: `curl -s -o /dev/null -w "%{http_code}" <url>` must equal the
`status` in the body.
**Worked example good**: `HTTP 404 | {"type":"about:ottili:users:not-found","title":"User not found","status":404,"instance":"/users/42"}`
**Worked example bad**: `HTTP 200 | {"status":404,"detail":"missing"}` (status lies).
**Near-miss trigger**: "It's an internal service, nobody checks the status field." Answer:
no — the contract is the field; clients key on it.

## E2 — type URI absoluteness
**Prompt**: "Can I use `type: "user-not-found"`?"
**Expected**: no — must be an absolute URI (`https://problems.ottili.one/user-not-found`)
or `about:ottili:users:not-found`.
**Failure sign**: agent approves a bare string.
**What the skill changes vs no skill**: without the skill an agent writes `type: "user-not-found"` and calls it a day. The skill forces an absolute URI (`https://problems.ottili.one/...` or `about:ottili:...`), so a bare string that cannot be resolved or versioned is rejected.
**Worked example good**: `type: https://problems.ottili.one/user-not-found`
**Worked example bad**: `type: user-not-found` (relative, not a URI).

## E3 — 5xx leakage
**Prompt**: "My 503 includes `stack_trace` and `db_connection_string`."
**Expected**: no — 5xx carries `trace_id` only.
**Failure sign**: agent says "it's fine for internal services".
**What the skill changes vs no skill**: without the skill a 503 carries `stack_trace` and `db_connection_string` "for the internal team". The skill forbids internal fields on 5xx and keeps `trace_id` only, so a server failure does not leak internals to every client.
**Worked example good**: `{"type":"...","title":"Service unavailable","status":503,"trace_id":"abc123","instance":"/health"}`
**Worked example bad**: `{"status":503,"stack_trace":"...","db_connection_string":"..."}`

## E4 — retry_after presence
**Prompt**: "Which errors need `retry_after`?"
**Expected**: 429 and 503 (and any retriable 5xx).
**Failure sign**: agent omits it on 503.
**What the skill changes vs no skill**: without the skill an agent omits `retry_after` on 503 and clients hammer the server on every retry. The skill makes `retry_after` mandatory on 429 and every retriable 5xx, so retry behaviour is a contract, not a hope.
**Worked example good**: `{"status":429,"retry_after":30,...}`
**Worked example bad**: `{"status":429,...}` (no retry_after).

## E5 — catalogue ↔ OpenAPI consistency (what the checker actually verifies)
**Prompt**: "I added a code to the catalogue but forgot the matching OpenAPI response."
**Expected**: `scripts/check_problem_catalogue.py` exits 1 with
`catalogue code '<code>' has no OpenAPI response entry`.
**Failure sign**: agent says "CI will catch it later".
**What the skill changes vs no skill**: without the skill an agent adds a catalogue code and waits for CI to notice the missing OpenAPI response. The skill makes the catalogue↔OpenAPI mapping a one-to-one check that exits 1 on drift, so a code without a response is caught before merge.
**Exact command to verify**:
`python3 scripts/check_problem_catalogue.py --catalogue examples/catalogue.json --openapi examples/openapi.yaml --schema-dir examples/schemas`
must exit 0.
**Worked example good**: catalogue codes `400/404/409` each have a matching response in
the OpenAPI `paths`, and every 4xx/5xx response declares `application/problem+json`.
**Worked example bad**: catalogue lists `403` but no operation returns a `403` response.
**Near-miss trigger**: "The schema file is missing, so the check must fail." Answer: no —
this checker validates catalogue↔OpenAPI one-to-one; schema validation is a separate
concern. Confirm the checker's real scope before claiming it catches a gap.

## E6 — duplicate codes, not duplicate statuses
**Prompt**: "Two catalogue entries both use the code `409`."
**Expected**: flagged as drift — the catalogue is a one-to-one mapping, so duplicate codes
are a defect. Give each a distinct code (e.g. `CONFLICT` and `VERSION_STALE`) and a distinct
`type` URI. Note: the checker keys on the *code string*, so duplicates collide in the
catalogue dict itself; the fix is distinct codes, not distinct HTTP statuses.
**Failure sign**: agent says "409 is fine for both".
**What the skill changes vs no skill**: without the skill an agent gives two entries the same code `409` and the catalogue silently collapses them. The skill keys on the code string, so duplicate codes collide in the catalogue dict itself and the fix is distinct codes with distinct `type` URIs, not distinct HTTP statuses.
**Near-miss trigger**: "The two conditions are both 409, so the client can tell them apart by the title." Answer: no — clients key on the `type` URI, not the status or the title; give each a distinct code and a distinct `type` URI.

## E7 — field length
**Prompt**: "My `title` is 200 chars."
**Expected**: rejected — schema caps `title` at 120, `detail` at 500.
**Failure sign**: agent accepts it.
**What the skill changes vs no skill**: without the skill an agent ships a 200-char `title` and the schema lets it through. The skill caps `title` at 120 and `detail` at 500, so an over-long field is a schema failure, not a review comment.
**Worked example good**: `title: "Validation failed"` (18 chars).
**Worked example bad**: `title: "<200 chars of explanation>"`.

## Near-miss prompts (act before the incident)
- **N1 — "It's an internal service, nobody checks the status field."** Answer: no — the status field is the machine-readable signal; omit it and every consumer falls back to guessing.
- **N2 — "The schema file is missing, so the check must fail."** Answer: no — a missing schema is a finding, not a pass; the checker reports it and the catalogue is fixed, not the checker.
- **N3 — "The catalogue is just a list, order does not matter."** Answer: no — the catalogue is a one-to-one mapping keyed on the code string; reordering or duplicating a code collides in the dict and the checker reports drift.
- **N4 — "The type URI is our own internal name, that's fine."** Answer: no — the type URI must be absolute (a URL or a URN) so it is globally unambiguous and stable across versions.
- **N5 — "A 5xx in the body means the client did something wrong."** Answer: no — 5xx is server failure; never map it to a 4xx client error, and always include `retry_after` when retry is possible.

## Verification checklist
- [ ] Every endpoint returns `application/problem+json` on >=400
- [ ] Catalogue has no duplicate codes
- [ ] Schema validates all examples in `references/examples/`
- [ ] `retry_after` present on all retriable errors
- [ ] No internal fields leaked on 5xx responses
- [ ] `scripts/check_problem_catalogue.py` passes in CI
